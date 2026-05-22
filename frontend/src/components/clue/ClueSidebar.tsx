import { useEffect, useMemo, useState } from 'react';

import { api, resolveApiUrl } from '../../api/client';
import { getTrustLabel } from '../../store/gameStore';
import type { Clue, DeductionPrompt, SessionSnapshot } from '../../types/game';
import { AssistantPanel } from '../assistant/AssistantPanel';

export type InvestigationTab = 'clues' | 'deduction' | 'notes' | 'assistant';

type VisualStatusItem = {
  asset_id: string;
  status: string;
  url: string | null;
};

type ClueSidebarProps = {
  snapshot: SessionSnapshot;
  selectedNpcId: string | null;
  busy: boolean;
  activeTab: InvestigationTab;
  onActiveTabChange: (tab: InvestigationTab) => void;
  onSubmitDeduction: (deductionId: string, selectedClueIds: string[]) => void;
  onCollapse?: () => void;
};

const tabs: Array<{ id: InvestigationTab; label: string }> = [
  { id: 'clues', label: '线索' },
  { id: 'deduction', label: '推理' },
  { id: 'notes', label: '笔记' },
  { id: 'assistant', label: '助手' },
];

const clueTypeLabels: Record<string, string> = {
  document: '文书',
  environment: '现场',
  behavior: '行为',
  evidence: '物证',
  institution: '制度',
  identity: '身份',
  rumor: '传闻',
  testimony: '证言',
};

function statusLabel(clue: Clue, presented: boolean): string {
  if (presented) {
    return '已出示';
  }
  if (clue.is_key) {
    return '关键线索';
  }
  return clueTypeLabels[clue.type] ?? '线索';
}

function clueAssetCandidates(clue: Clue): string[] {
  const ids = [clue.visual_asset_id, clue.clue_id];
  if (clue.clue_id === 'clue_red_seal') {
    ids.push('clue_red_seal_fragment');
  }
  return ids.filter((id): id is string => Boolean(id));
}

function clueImageUrl(clue: Clue, statusMap: Map<string, VisualStatusItem>): string {
  const generated = clueAssetCandidates(clue)
    .map((assetId) => statusMap.get(assetId))
    .find((item) => item?.status === 'generated' && item.url);
  if (!generated?.url) {
    return '';
  }
  return resolveApiUrl(generated.url);
}

function buildKnownFacts(snapshot: SessionSnapshot): string[] {
  const facts = [
    ...snapshot.clues.slice(-4).map((clue) => `已发现「${clue.title}」：${clue.display_text}`),
    ...snapshot.combo_summaries.slice(-3).map((combo) => `线索组合「${combo.result_title}」：${combo.result_text}`),
    ...snapshot.deduction_summaries.slice(-3).map((deduction) => `推理「${deduction.question}」：${deduction.success_text}`),
    ...snapshot.dialogue_turns.slice(-3).map((turn) => `${turn.npc_name}提到：${turn.npc_response}`),
  ];
  return facts.length > 0 ? facts : ['案卷尚未形成稳定事实，先从当前地点的可疑物件查起。'];
}

export function ClueSidebar({
  snapshot,
  selectedNpcId,
  busy,
  activeTab,
  onActiveTabChange,
  onSubmitDeduction,
  onCollapse,
}: ClueSidebarProps) {
  const [visualStatuses, setVisualStatuses] = useState<VisualStatusItem[]>([]);
  const [selectedDeductionId, setSelectedDeductionId] = useState('');
  const [selectedClueIds, setSelectedClueIds] = useState<string[]>([]);
  const [deductionNotice, setDeductionNotice] = useState('');

  useEffect(() => {
    let mounted = true;
    api.getVisualStatus()
      .then((result) => {
        if (mounted) {
          setVisualStatuses(result.assets as VisualStatusItem[]);
        }
      })
      .catch(() => {
        if (mounted) {
          setVisualStatuses([]);
        }
      });
    return () => {
      mounted = false;
    };
  }, [snapshot.session_id, snapshot.clues.length]);

  const statusMap = useMemo(
    () => new Map(visualStatuses.map((item) => [item.asset_id, item])),
    [visualStatuses],
  );

  const presentedClueIds = useMemo(
    () => new Set(snapshot.dialogue_turns.flatMap((turn) => turn.presented_clue_ids)),
    [snapshot.dialogue_turns],
  );
  const knownFacts = useMemo(() => buildKnownFacts(snapshot), [snapshot]);
  const selectedNpc = snapshot.scene_npcs.find((npc) => npc.npc_id === selectedNpcId) ?? snapshot.scene_npcs[0];
  const activeDeduction = useMemo<DeductionPrompt | undefined>(
    () => snapshot.available_deductions.find((item) => item.deduction_id === selectedDeductionId) ?? snapshot.available_deductions[0],
    [selectedDeductionId, snapshot.available_deductions],
  );

  useEffect(() => {
    if (!snapshot.available_deductions.length) {
      setSelectedDeductionId('');
      setSelectedClueIds([]);
      return;
    }
    if (!snapshot.available_deductions.some((item) => item.deduction_id === selectedDeductionId)) {
      setSelectedDeductionId(snapshot.available_deductions[0].deduction_id);
      setSelectedClueIds([]);
    }
  }, [selectedDeductionId, snapshot.available_deductions]);

  const toggleClue = (clueId: string) => {
    setDeductionNotice('');
    setSelectedClueIds((current) => (
      current.includes(clueId) ? current.filter((item) => item !== clueId) : [...current, clueId].slice(-5)
    ));
  };

  const submitDeduction = () => {
    if (!activeDeduction) {
      return;
    }
    if (selectedClueIds.length === 0) {
      setDeductionNotice('请先选择至少一条证据。');
      return;
    }
    setDeductionNotice('推理已提交，结果会在底部对话框中显示。');
    onSubmitDeduction(activeDeduction.deduction_id, selectedClueIds);
  };

  return (
    <aside className="investigation-panel" aria-label="右侧调查栏">
      <header className="investigation-panel-toolbar">
        <span>案卷调查</span>
        {onCollapse ? <button type="button" onClick={onCollapse}>收起</button> : null}
      </header>
      <nav className="investigation-tabs" aria-label="调查栏分页">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={activeTab === tab.id ? 'active' : ''}
            onClick={() => onActiveTabChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="investigation-panel-body">
        {activeTab === 'clues' ? (
          <section className="investigation-tab-content clue-tab-content">
            <header className="side-panel-heading">
              <p className="meta-label">已发现线索</p>
              <h3>{snapshot.clues.length} 条</h3>
            </header>
            <div className="clue-card-list">
              {snapshot.clues.length > 0 ? snapshot.clues.map((clue) => {
                const imageUrl = clueImageUrl(clue, statusMap);
                const presented = presentedClueIds.has(clue.clue_id);
                return (
                  <article key={clue.clue_id} className={clue.is_key ? 'investigation-clue-card key' : 'investigation-clue-card'}>
                    <div className="investigation-clue-image">
                      {imageUrl ? <img src={imageUrl} alt={`${clue.title}线索图`} /> : <span>线索图待生成</span>}
                    </div>
                    <div className="investigation-clue-copy">
                      <div className="detail-head">
                        <strong>{clue.title}</strong>
                        <span>{statusLabel(clue, presented)}</span>
                      </div>
                      <p>{clue.display_text}</p>
                      <div className="clue-tag-row">
                        <em>{clueTypeLabels[clue.type] ?? '线索'}</em>
                        {clue.is_key ? <em>关键</em> : null}
                        {presented ? <em>已出示</em> : null}
                      </div>
                    </div>
                  </article>
                );
              }) : (
                <div className="empty-card dark-empty">线索尚空，先调查当前场景的可疑物件。</div>
              )}
            </div>
          </section>
        ) : null}

        {activeTab === 'deduction' ? (
          <section className="investigation-tab-content">
            <header className="side-panel-heading">
              <p className="meta-label">主动推理</p>
              <h3>{snapshot.available_deductions.length > 0 ? '可提交疑团' : '暂无可提交疑团'}</h3>
            </header>
            {snapshot.available_deductions.length > 0 && activeDeduction ? (
              <>
                <div className="deduction-question-list">
                  {snapshot.available_deductions.map((deduction) => (
                    <button
                      key={deduction.deduction_id}
                      type="button"
                      className={activeDeduction.deduction_id === deduction.deduction_id ? 'active' : ''}
                      onClick={() => {
                        setSelectedDeductionId(deduction.deduction_id);
                        setSelectedClueIds([]);
                        setDeductionNotice('');
                      }}
                      disabled={busy}
                    >
                      {deduction.question}
                    </button>
                  ))}
                </div>
                <p className="side-note">选择能支撑「{activeDeduction.question}」的证据。</p>
                <div className="deduction-evidence-grid">
                  {snapshot.clues.map((clue) => (
                    <button
                      key={clue.clue_id}
                      type="button"
                      className={selectedClueIds.includes(clue.clue_id) ? 'active' : ''}
                      onClick={() => toggleClue(clue.clue_id)}
                      disabled={busy}
                    >
                      {clue.title}
                    </button>
                  ))}
                </div>
                <button type="button" className="primary-button panel-primary-action" onClick={submitDeduction} disabled={busy}>
                  提交推理
                </button>
                {deductionNotice ? <p className="side-note">{deductionNotice}</p> : null}
              </>
            ) : (
              <div className="empty-card dark-empty">继续调查或盘问人物，等证据链足够时再提交推理。</div>
            )}

            {snapshot.deduction_summaries.length > 0 ? (
              <div className="completed-deduction-list">
                <strong>已完成推理</strong>
                {snapshot.deduction_summaries.map((item) => (
                  <article key={item.deduction_id}>
                    <span>{item.question}</span>
                    <p>{item.success_text}</p>
                  </article>
                ))}
              </div>
            ) : null}
          </section>
        ) : null}

        {activeTab === 'notes' ? (
          <section className="investigation-tab-content">
            <header className="side-panel-heading">
              <p className="meta-label">案情笔记</p>
              <h3>已知事实</h3>
            </header>
            <ul className="note-fact-list">
              {knownFacts.map((fact) => <li key={fact}>{fact}</li>)}
            </ul>
            {selectedNpc ? (
              <article className="current-person-note">
                <strong>当前人物：{selectedNpc.name}</strong>
                <span>{selectedNpc.public_identity} · 信任：{getTrustLabel(snapshot.state.npc_trust[selectedNpc.npc_id] ?? 0)}</span>
                <p>{selectedNpc.background_suspicion}</p>
              </article>
            ) : null}
          </section>
        ) : null}

        {activeTab === 'assistant' ? (
          <AssistantPanel snapshot={snapshot} compact />
        ) : null}
      </div>
    </aside>
  );
}

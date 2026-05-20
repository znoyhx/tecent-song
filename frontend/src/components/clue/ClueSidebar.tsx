import { useEffect, useMemo, useRef, useState } from 'react';

import { resolveApiUrl } from '../../api/client';
import { stageDescriptions, getTrustLabel } from '../../store/gameStore';
import type { Clue, NPCProfile, SessionSnapshot } from '../../types/game';
import { ClueHotspotText } from '../dialogue/ClueHotspotText';


type ClueSidebarProps = {
  snapshot: SessionSnapshot;
  selectedNpcId: string | null;
  busy: boolean;
  onEnterScene: (sceneId: string) => void;
  onInspect: (sceneId: string, hotspotId: string, clueId?: string | null) => void;
  onSelectNpc: (npcId: string) => void;
  onSubmitDeduction: (deductionId: string, selectedClueIds: string[]) => void;
};

type PrimaryTab = 'dossier' | 'location' | 'investigation';
type DossierSubTab = 'case' | 'clues' | 'people';

const primaryTabs: Array<{ id: PrimaryTab; label: string }> = [
  { id: 'dossier', label: '案卷' },
  { id: 'location', label: '地点' },
  { id: 'investigation', label: '调查' },
];

const dossierSubTabs: Array<{ id: DossierSubTab; label: string }> = [
  { id: 'case', label: '案卷' },
  { id: 'clues', label: '线索' },
  { id: 'people', label: '身份介绍' },
];

const stageOrder: Record<string, number> = {
  intro: 0,
  investigation: 1,
  reversal: 2,
  choice: 3,
  ending: 4,
};

function buildKnownFacts(snapshot: SessionSnapshot): string[] {
  const clueFacts = snapshot.clues.slice(-3).map((clue) => `你已发现「${clue.title}」。`);
  const comboFacts = snapshot.combo_summaries.slice(-2).map((combo) => combo.result_text);
  const deductionFacts = snapshot.deduction_summaries.slice(-2).map((deduction) => deduction.success_text);
  const dialogueFacts = snapshot.dialogue_turns.slice(-2).map((turn) => `${turn.npc_name}提到：${turn.npc_response}`);
  const facts = [...clueFacts, ...comboFacts, ...deductionFacts, ...dialogueFacts];
  return facts.length > 0 ? facts : ['案卷尚未形成稳定事实，请先从右侧【调查】查看账桌与旧书箱。'];
}

function getClueImageUrl(clue?: Clue): string {
  if (!clue) {
    return '';
  }
  const withAssetVersion = (url: string) => {
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}asset_v=clue-png-v2`;
  };
  if (clue.visual_asset_url) {
    return withAssetVersion(resolveApiUrl(clue.visual_asset_url));
  }
  if (clue.visual_asset_id) {
    return withAssetVersion(resolveApiUrl(`/api/visual/assets/${clue.visual_asset_id}`));
  }
  return '';
}

function isProfileRevealUnlocked(
  reveal: NonNullable<NPCProfile['profile_progression']>[string][number],
  snapshot: SessionSnapshot,
): boolean {
  const requiredStage = reveal.required_stage;
  if (requiredStage && (stageOrder[snapshot.state.current_stage] ?? 0) < (stageOrder[requiredStage] ?? 0)) {
    return false;
  }
  const discovered = new Set(snapshot.state.discovered_clue_ids);
  const flags = new Set(snapshot.state.flags);
  if ((reveal.required_clue_ids ?? []).some((clueId) => !discovered.has(clueId))) {
    return false;
  }
  if ((reveal.required_flags ?? []).some((flag) => !flags.has(flag))) {
    return false;
  }
  return true;
}

function resolveNpcProfileValue(npc: NPCProfile, field: keyof Pick<NPCProfile, 'appearance' | 'personality' | 'background_suspicion' | 'case_connection' | 'event_behavior'>, snapshot: SessionSnapshot): string {
  const baseValue = String(npc[field] ?? '');
  const reveals = npc.profile_progression?.[field] ?? [];
  const unlocked = reveals.filter((reveal) => isProfileRevealUnlocked(reveal, snapshot));
  return unlocked.length > 0 ? unlocked[unlocked.length - 1].text : baseValue;
}

function buildNpcIdentityRows(npc: NPCProfile, snapshot: SessionSnapshot): Array<{ label: string; value: string }> {
  return [
    { label: '身份', value: npc.public_identity },
    { label: '外貌', value: resolveNpcProfileValue(npc, 'appearance', snapshot) },
    { label: '性格', value: resolveNpcProfileValue(npc, 'personality', snapshot) },
    { label: '背景疑点', value: resolveNpcProfileValue(npc, 'background_suspicion', snapshot) },
    { label: '与案件关联', value: resolveNpcProfileValue(npc, 'case_connection', snapshot) },
    { label: '事件表现', value: resolveNpcProfileValue(npc, 'event_behavior', snapshot) },
  ].filter((row) => row.value.trim().length > 0);
}


export function ClueSidebar({ snapshot, selectedNpcId, busy, onEnterScene, onInspect, onSelectNpc, onSubmitDeduction }: ClueSidebarProps) {
  const [open, setOpen] = useState(false);
  const [activePrimaryTab, setActivePrimaryTab] = useState<PrimaryTab>('dossier');
  const [activeDossierTab, setActiveDossierTab] = useState<DossierSubTab>('case');
  const [selectedClueId, setSelectedClueId] = useState<string>('');
  const [selectedDeductionId, setSelectedDeductionId] = useState<string>('');
  const [selectedDeductionClueIds, setSelectedDeductionClueIds] = useState<string[]>([]);
  const [deductionNotice, setDeductionNotice] = useState('');
  const [clueImageFailed, setClueImageFailed] = useState(false);
  const sidebarRef = useRef<HTMLElement | null>(null);

  const selectedClue = useMemo<Clue | undefined>(
    () => snapshot.clues.find((clue) => clue.clue_id === selectedClueId) ?? snapshot.clues[0],
    [selectedClueId, snapshot.clues],
  );
  const selectedClueImageUrl = useMemo(() => getClueImageUrl(selectedClue), [selectedClue]);

  const knownFacts = useMemo(() => buildKnownFacts(snapshot), [snapshot]);
  const selectedDeduction = useMemo(
    () => snapshot.available_deductions.find((deduction) => deduction.deduction_id === selectedDeductionId) ?? snapshot.available_deductions[0],
    [selectedDeductionId, snapshot.available_deductions],
  );
  const presentedClueIds = useMemo(
    () => new Set(snapshot.dialogue_turns.flatMap((turn) => turn.presented_clue_ids)),
    [snapshot.dialogue_turns],
  );

  const clueTitleMap = useMemo(
    () => new Map(snapshot.clues.map((clue) => [clue.clue_id, clue.title])),
    [snapshot.clues],
  );
  const hasNewClueCue = snapshot.clues.some((clue) => clue.red_highlight || clue.is_key);
  const scene = snapshot.scene;
  const activePrimaryLabel = primaryTabs.find((tab) => tab.id === activePrimaryTab)?.label ?? '案卷';
  const stageDescription = stageDescriptions[snapshot.state.current_stage] ?? snapshot.stage_label;
  const completedSceneClues = snapshot.clues.filter((clue) => clue.source_scene_id === scene.scene_id);

  useEffect(() => {
    if (!snapshot.clues.length) {
      setSelectedClueId('');
      return;
    }
    if (!snapshot.clues.some((clue) => clue.clue_id === selectedClueId)) {
      setSelectedClueId(snapshot.clues[0].clue_id);
    }
  }, [selectedClueId, snapshot.clues]);

  useEffect(() => {
    setClueImageFailed(false);
  }, [selectedClue?.clue_id, selectedClueImageUrl]);

  useEffect(() => {
    if (!snapshot.available_deductions.length) {
      setSelectedDeductionId('');
      setSelectedDeductionClueIds([]);
      return;
    }
    if (!snapshot.available_deductions.some((deduction) => deduction.deduction_id === selectedDeductionId)) {
      setSelectedDeductionId(snapshot.available_deductions[0].deduction_id);
      setSelectedDeductionClueIds([]);
    }
  }, [selectedDeductionId, snapshot.available_deductions]);

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    const handlePointerDown = (event: PointerEvent) => {
      const target = event.target;
      if (target instanceof Node && sidebarRef.current?.contains(target)) {
        return;
      }
      setOpen(false);
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpen(false);
      }
    };

    document.addEventListener('pointerdown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open]);


  const handlePrimaryClick = (tabId: PrimaryTab) => {
    setActivePrimaryTab(tabId);
    setOpen(true);
  };

  const handleContinue = () => {
    const nextHighlight = scene.highlights[0];
    if (nextHighlight) {
      onInspect(scene.scene_id, nextHighlight.hotspot_id, nextHighlight.clue_id);
      return;
    }
    const nextHotspot = scene.hotspots[0];
    if (nextHotspot) {
      onInspect(scene.scene_id, nextHotspot.hotspot_id, nextHotspot.clue_ids[0] ?? null);
    }
  };

  const toggleDeductionClue = (clueId: string) => {
    setDeductionNotice('');
    setSelectedDeductionClueIds((current) => (
      current.includes(clueId) ? current.filter((item) => item !== clueId) : [...current, clueId].slice(-5)
    ));
  };

  const handleSubmitDeduction = () => {
    if (!selectedDeduction) {
      return;
    }
    if (selectedDeductionClueIds.length === 0) {
      setDeductionNotice('请先选择至少一条证据。');
      return;
    }
    setDeductionNotice('推理已提交，结果会显示在底部叙事栏。');
    onSubmitDeduction(selectedDeduction.deduction_id, selectedDeductionClueIds);
  };

  return (
    <aside ref={sidebarRef} className={open ? 'case-dossier open' : 'case-dossier'} aria-label="右侧信息栏" aria-expanded={open}>
      <nav className="sidebar-rail" aria-label="一级栏目">
        {primaryTabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={[
              'sidebar-rail-button',
              activePrimaryTab === tab.id ? 'active' : '',
              tab.id === 'dossier' && hasNewClueCue ? 'has-new-clue' : '',
            ].filter(Boolean).join(' ')}
            onClick={() => handlePrimaryClick(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="dossier-paper">
        <header className="dossier-header">
          <button type="button" className="sidebar-collapse-button" onClick={() => setOpen(false)}>收起</button>
          <p className="meta-label">右侧栏目</p>
          <h3>{activePrimaryLabel}</h3>
          <span>书坊焚稿案 · {snapshot.stage_label} · {snapshot.clues.length} 条线索</span>
        </header>

        {activePrimaryTab === 'dossier' ? (
          <>
            <nav className="dossier-tabs dossier-subtabs" aria-label="案卷二级分类">
              {dossierSubTabs.map((tab) => (
                <button key={tab.id} type="button" className={activeDossierTab === tab.id ? 'active' : ''} onClick={() => setActiveDossierTab(tab.id)}>
                  {tab.label}
                </button>
              ))}
            </nav>

            {activeDossierTab === 'case' ? (
              <div className="dossier-section paper-list">
                <article className="detail-card dossier-note">
                  <strong>当前事件</strong>
                  <p>书坊焚稿案</p>
                  <p className="detail-note">目标：{snapshot.current_goal}</p>
                  <p className="detail-tag">剧情阶段：{snapshot.stage_label} · {stageDescription}</p>
                </article>
                <article className="detail-card dossier-note">
                  <strong>已知事实摘要</strong>
                  <ul className="fact-list">
                    {knownFacts.map((fact) => <li key={fact}>{fact}</li>)}
                  </ul>
                </article>
                <article className="detail-card dossier-note">
                  <strong>主动推理</strong>
                  {snapshot.available_deductions.length > 0 && selectedDeduction ? (
                    <>
                      <div className="sidebar-action-list compact-actions">
                        {snapshot.available_deductions.map((deduction) => (
                          <button
                            key={deduction.deduction_id}
                            type="button"
                            className={deduction.deduction_id === selectedDeduction.deduction_id ? 'side-action active' : 'side-action'}
                            onClick={() => {
                              setSelectedDeductionId(deduction.deduction_id);
                              setSelectedDeductionClueIds([]);
                              setDeductionNotice('');
                            }}
                            disabled={busy}
                          >
                            {deduction.question}
                          </button>
                        ))}
                      </div>
                      <p className="detail-note">选择能支撑「{selectedDeduction.question}」的证据。</p>
                      <div className="sidebar-action-list compact-actions">
                        {snapshot.clues.map((clue) => (
                          <button
                            key={clue.clue_id}
                            type="button"
                            className={selectedDeductionClueIds.includes(clue.clue_id) ? 'side-action active' : 'side-action'}
                            onClick={() => toggleDeductionClue(clue.clue_id)}
                            disabled={busy}
                          >
                            {selectedDeductionClueIds.includes(clue.clue_id) ? '已选：' : '证据：'}{clue.title}
                          </button>
                        ))}
                      </div>
                      <button type="button" className="side-action danger" onClick={handleSubmitDeduction} disabled={busy}>
                        提交推理
                      </button>
                      {deductionNotice ? <p className="detail-tag">{deductionNotice}</p> : null}
                    </>
                  ) : (
                    <p className="detail-note">当前还没有证据足够的疑团，继续调查或盘问人物。</p>
                  )}
                </article>
                {snapshot.deduction_summaries.length > 0 ? (
                  <article className="detail-card dossier-note">
                    <strong>思维疑团</strong>
                    <ul className="fact-list">
                      {snapshot.deduction_summaries.slice(-4).map((deduction) => (
                        <li key={deduction.deduction_id}>【{deduction.question}】{deduction.success_text}</li>
                      ))}
                    </ul>
                  </article>
                ) : null}
                {snapshot.combo_summaries.length > 0 ? (
                  <article className="detail-card dossier-note">
                    <strong>线索组合</strong>
                    <ul className="fact-list">
                      {snapshot.combo_summaries.slice(-4).map((combo) => (
                        <li key={combo.combo_id}>【{combo.result_title}】{combo.result_text}</li>
                      ))}
                    </ul>
                  </article>
                ) : null}
                <details className="detail-card dossier-note history-drawer">
                  <summary>查看完整会话记录</summary>
                  <div className="history-list">
                    {snapshot.dialogue_turns.length > 0 ? (
                      snapshot.dialogue_turns.map((turn) => (
                        <article key={turn.turn_id}>
                          <span>你：{turn.player_message}</span>
                          <strong>{turn.npc_name}：{turn.npc_response}</strong>
                        </article>
                      ))
                    ) : (
                      <p className="detail-note">尚无历史对话。</p>
                    )}
                  </div>
                </details>
              </div>
            ) : null}

            {activeDossierTab === 'clues' ? (
              <div className="dossier-section">
                <div className="clue-list paper-list">
                  {snapshot.clues.length > 0 ? (
                    snapshot.clues.map((clue) => (
                      <button
                        key={clue.clue_id}
                        type="button"
                        className={[
                          'clue-item',
                          clue.is_key ? 'key' : '',
                          clue.clue_id === selectedClue?.clue_id ? 'active' : '',
                          presentedClueIds.has(clue.clue_id) ? 'presented' : '',
                        ].filter(Boolean).join(' ')}
                        onClick={() => setSelectedClueId(clue.clue_id)}
                      >
                        <span>{clue.title}</span>
                        <small>{presentedClueIds.has(clue.clue_id) ? '已出示' : clue.is_key ? '朱砂关键' : clue.source_npc_id ? '证言' : '物证'}</small>
                      </button>
                    ))
                  ) : (
                    <div className="empty-card">线索尚空，纸页仍湿。</div>
                  )}
                </div>

                {selectedClue ? (
                  <article className="detail-card dossier-note">
                    <div className="detail-head">
                      <strong>{selectedClue.title}</strong>
                      {presentedClueIds.has(selectedClue.clue_id) ? <span className="key-badge presented-badge">已出示</span> : null}
                      {selectedClue.red_highlight ? <span className="key-badge">红字</span> : null}
                    </div>
                    {selectedClueImageUrl && !clueImageFailed ? (
                      <figure className="clue-visual-card">
                        <img src={selectedClueImageUrl} alt={`${selectedClue.title}线索图`} onError={() => setClueImageFailed(true)} />
                        <figcaption>{selectedClue.visual_status === 'generated' ? '已生成线索图' : '证物线索图'}</figcaption>
                      </figure>
                    ) : selectedClue.visual_asset_id ? (
                      <div className="clue-visual-fallback">线索图暂不可用，已保留文字证据。</div>
                    ) : null}
                    <p>{selectedClue.display_text}</p>
                    <p className="detail-note">{selectedClue.detail}</p>

                    <p className="detail-tag">关键文本：{selectedClue.highlight_text}</p>
                    {(() => {
                      const relatedTitles = selectedClue.related_clue_ids
                        .map((id) => clueTitleMap.get(id))
                        .filter((title): title is string => Boolean(title));
                      const undiscoveredCount = selectedClue.related_clue_ids.length - relatedTitles.length;

                      if (relatedTitles.length === 0 && undiscoveredCount === 0) {
                        return null;
                      }

                      const relatedSummary = [
                        ...relatedTitles,
                        ...(undiscoveredCount > 0 ? [`${undiscoveredCount} 条未发现的相关线索`] : []),
                      ].join('、');

                      return <p className="detail-tag">可能相关：{relatedSummary}</p>;
                    })()}
                  </article>
                ) : null}
              </div>
            ) : null}

            {activeDossierTab === 'people' ? (
              <div className="dossier-section paper-list">
                {snapshot.scene_npcs.length > 0 ? (
                  snapshot.scene_npcs.map((npc) => {
                    const identityRows = buildNpcIdentityRows(npc, snapshot);
                    return (
                      <article key={npc.npc_id} className={npc.npc_id === selectedNpcId ? 'detail-card dossier-note active-person' : 'detail-card dossier-note'}>
                        <div className="detail-head">
                          <strong>{npc.name}</strong>
                          <span className="key-badge subtle">{getTrustLabel(snapshot.state.npc_trust[npc.npc_id] ?? 0)}</span>
                        </div>
                        <strong>身份介绍</strong>
                        <div className="fact-list">
                          {identityRows.map((row) => (
                            <p key={row.label} className="detail-note"><strong>{row.label}：</strong>{row.value}</p>
                          ))}
                        </div>
                        <button type="button" className="side-action" onClick={() => onSelectNpc(npc.npc_id)} disabled={busy || npc.npc_id === selectedNpcId}>
                          {npc.npc_id === selectedNpcId ? '当前对话对象' : '切换对话对象'}
                        </button>
                      </article>
                    );
                  })
                ) : (
                  <div className="empty-card">此处暂无可盘问人物。</div>
                )}
              </div>
            ) : null}
          </>
        ) : null}

        {activePrimaryTab === 'location' ? (
          <div className="dossier-section paper-list primary-panel-content">
            <article className="detail-card dossier-note">
              <strong>当前地点：{scene.name}</strong>
              <p>{scene.description}</p>
              <p className="detail-note">
                <ClueHotspotText text={scene.scene_text} sceneId={scene.scene_id} highlights={scene.highlights} busy={busy} onInspect={onInspect} />
              </p>
            </article>
            <article className="detail-card dossier-note">
              <strong>可前往地点</strong>
              <div className="sidebar-action-list">
                {snapshot.available_scenes.map((item) => (
                  <button
                    key={item.scene_id}
                    type="button"
                    className={item.scene_id === scene.scene_id ? 'side-action active' : 'side-action'}
                    onClick={() => onEnterScene(item.scene_id)}
                    disabled={busy || item.scene_id === scene.scene_id}
                  >
                    {item.name}
                  </button>
                ))}
              </div>
            </article>
            <article className="detail-card dossier-note">
              <strong>场景内可疑物件</strong>
              <ul className="fact-list">
                {scene.hotspots.length > 0 ? scene.hotspots.map((hotspot) => (
                  <li key={hotspot.hotspot_id}>
                    {hotspot.label}{hotspot.description ? `：${hotspot.description}` : ''}
                  </li>
                )) : <li>暂无可疑物件。</li>}
              </ul>
            </article>
          </div>
        ) : null}

        {activePrimaryTab === 'investigation' ? (
          <div className="dossier-section paper-list primary-panel-content">
            <article className="detail-card dossier-note">
              <strong>可执行调查</strong>
              <div className="sidebar-action-list">
                {scene.hotspots.map((hotspot) => {
                  const missingCount = (hotspot.required_clue_ids ?? []).filter((clueId) => !snapshot.state.discovered_clue_ids.includes(clueId)).length;
                  return (
                    <button
                      key={hotspot.hotspot_id}
                      type="button"
                      className="side-action danger"
                      title={hotspot.description || hotspot.label}
                      onClick={() => onInspect(scene.scene_id, hotspot.hotspot_id, hotspot.clue_ids[0] ?? null)}
                      disabled={busy || missingCount > 0}
                    >
                      {hotspot.label}{missingCount > 0 ? `（缺 ${missingCount} 条前置）` : ''}
                    </button>
                  );
                })}
                <button type="button" className="side-action danger" onClick={handleContinue} disabled={busy || (!scene.highlights.length && !scene.hotspots.length)}>
                  继续推进
                </button>
              </div>
            </article>
            <article className="detail-card dossier-note">
              <strong>已完成调查</strong>
              <ul className="fact-list">
                {completedSceneClues.length > 0 ? completedSceneClues.map((clue) => <li key={clue.clue_id}>{clue.title}</li>) : <li>当前地点尚无确认发现。</li>}
              </ul>
            </article>
          </div>
        ) : null}
      </div>
    </aside>
  );
}

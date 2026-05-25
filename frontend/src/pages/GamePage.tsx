import { useMemo, useState, type PointerEvent as ReactPointerEvent, type ReactNode } from 'react';

import { resolveApiUrl, visualAssetUrl } from '../api/client';
import { AssistantPanel } from '../components/assistant/AssistantPanel';
import { ClueSidebar, type InvestigationTab } from '../components/clue/ClueSidebar';
import { DialoguePanel } from '../components/dialogue/DialoguePanel';
import { DemoEvidencePanel } from '../components/debug/DemoEvidencePanel';
import { EndingPanel } from '../components/ending/EndingPanel';
import { PhaserStage } from '../components/scene/PhaserStage';
import { ScenePanel } from '../components/scene/ScenePanel';
import { getTrustLabel, stageDescriptions } from '../store/gameStore';
import type { DialogueMessageSource, NPCProfile, Scene, SessionSnapshot } from '../types/game';

type GamePageProps = {
  snapshot: SessionSnapshot;
  selectedNpcId: string | null;
  suggestedQuestions: string[];
  highlightClues: SessionSnapshot['dialogue_turns'][number]['highlight_clues'];
  redTexts: string[];
  actionNotice: string;
  debugEnabled: boolean;
  busy: boolean;
  onEnterScene: (sceneId: string) => void;
  onInspect: (sceneId: string, hotspotId: string, clueId?: string | null) => void;
  onSelectNpc: (npcId: string) => void;
  onSendDialogue: (npcId: string, message: string, presentedClueIds: string[], messageSource: DialogueMessageSource) => void;
  onSubmitDeduction: (deductionId: string, selectedClueIds: string[]) => void;
  onChoose: (choiceId: string) => void;
  onRestart: () => void;
  onToggleDebug?: () => void;
};

type OverlayPanel = 'scenes' | 'people' | 'tasks' | 'assistant' | null;
type CommandIconName = 'scene' | 'people' | 'task' | 'assistant';

const stageWeight: Record<string, number> = {
  intro: 0,
  investigation: 20,
  reversal: 52,
  choice: 82,
  ending: 100,
};

const npcSceneCutoutAssetIds: Record<string, string> = {
  npc_owner: 'npc_xu_owner_cutout',
  npc_worker: 'npc_ashen_worker_cutout',
  npc_scholar: 'npc_guwen_scholar_cutout',
  npc_jinyiwei: 'npc_luzheng_jinyiwei_cutout',
};

const mainSurfaceIgnoreSelector = [
  '.left-command-bar',
  '.investigation-panel',
  '.right-panel-rail',
  '.dialogue-box',
  '.game-top-status',
  '.game-modal-backdrop',
  '.debug-toggle-button',
  '.choice-overlay',
].join(', ');

function sceneImageUrl(scene: Scene): string {
  if (scene.visual_status !== 'generated' && scene.visual_status !== 'approved') {
    return '';
  }
  if (scene.visual_asset_url) {
    return resolveApiUrl(scene.visual_asset_url);
  }
  if (scene.visual_asset_id && !scene.visual_asset_id.startsWith('asset_')) {
    return resolveApiUrl(`/api/visual/assets/${scene.visual_asset_id}`);
  }
  return '';
}

function npcDisplayImage(npc: NPCProfile): { url: string; source: 'scene-cutout' | 'portrait' } {
  const sceneCutoutAssetId = npcSceneCutoutAssetIds[npc.npc_id];
  if (sceneCutoutAssetId) {
    return { url: visualAssetUrl(sceneCutoutAssetId), source: 'scene-cutout' };
  }

  const directUrl = npc.portraitUrl ?? npc.fallbackPortraitUrl ?? npc.imageUrl ?? npc.avatarUrl ?? npc.visual_asset_url;
  if (directUrl) {
    return { url: resolveApiUrl(directUrl), source: 'portrait' };
  }
  if (npc.visual_asset_id) {
    return { url: resolveApiUrl(`/api/visual/assets/${npc.visual_asset_id}`), source: 'portrait' };
  }
  return { url: '', source: 'portrait' };
}

function investigationProgress(snapshot: SessionSnapshot): number {
  const cluePool = new Set<string>();
  snapshot.available_scenes.forEach((scene) => {
    scene.hotspots.forEach((hotspot) => hotspot.clue_ids.forEach((clueId) => cluePool.add(clueId)));
  });
  snapshot.state.discovered_clue_ids.forEach((clueId) => cluePool.add(clueId));
  const stageBase = stageWeight[snapshot.state.current_stage] ?? 0;
  const stageSpan = snapshot.state.current_stage === 'choice' ? 14 : 26;
  const localProgress = cluePool.size > 0 ? snapshot.state.discovered_clue_ids.length / cluePool.size : 0;
  return Math.max(0, Math.min(100, Math.round(stageBase + localProgress * stageSpan)));
}

function hasUndiscoveredSceneClue(scene: Scene, snapshot: SessionSnapshot): boolean {
  const discovered = new Set(snapshot.state.discovered_clue_ids);
  return scene.hotspots.some((hotspot) => hotspot.clue_ids.some((clueId) => !discovered.has(clueId)));
}

function isProfileRevealUnlocked(
  reveal: NonNullable<NPCProfile['profile_progression']>[string][number],
  snapshot: SessionSnapshot,
): boolean {
  const requiredStage = reveal.required_stage;
  if (requiredStage && (stageWeight[snapshot.state.current_stage] ?? 0) < (stageWeight[requiredStage] ?? 0)) {
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

function profileValue(npc: NPCProfile, field: keyof Pick<NPCProfile, 'appearance' | 'personality' | 'background_suspicion' | 'case_connection' | 'event_behavior'>, snapshot: SessionSnapshot): string {
  const reveals = npc.profile_progression?.[field] ?? [];
  const unlocked = reveals.filter((reveal) => isProfileRevealUnlocked(reveal, snapshot));
  return unlocked.length > 0 ? unlocked[unlocked.length - 1].text : String(npc[field] ?? '');
}

function TopStatusBar({ snapshot }: { snapshot: SessionSnapshot }) {
  const progress = investigationProgress(snapshot);
  const identity = snapshot.player_identity?.display_name ?? snapshot.player_role.name;

  return (
    <header className="game-top-status" aria-label="顶部状态栏">
      <div className="top-status-main">
        <strong>{snapshot.dynasty.name} · {snapshot.dynasty.period_label}</strong>
        <span>/ {snapshot.scene.name}</span>
        <span>身份：{identity}</span>
        <span>当前目标：{snapshot.current_goal}</span>
      </div>
      <div className="top-status-progress" aria-label="调查进度">
        <span>调查进度</span>
        <strong>{progress}%</strong>
        <i style={{ width: `${progress}%` }} />
      </div>
      <button type="button" className="status-icon-button" aria-label="设置">设置</button>
    </header>
  );
}

function CommandIcon({ name }: { name: CommandIconName }) {
  if (name === 'scene') {
    return (
      <svg viewBox="0 0 32 32" aria-hidden="true">
        <path d="M6 13.5h20v11H6z" />
        <path d="M9 13.5v-5h14v5" />
        <path d="M11 24.5v-5h10v5" />
        <path d="M5 11h22" />
        <path d="M10 8.5 12.5 5h7L22 8.5" />
      </svg>
    );
  }
  if (name === 'people') {
    return (
      <svg viewBox="0 0 32 32" aria-hidden="true">
        <path d="M16 15.5a5.2 5.2 0 1 0 0-10.4 5.2 5.2 0 0 0 0 10.4Z" />
        <path d="M7.5 26.5c1.2-5.4 4.2-8.1 8.5-8.1s7.3 2.7 8.5 8.1" />
      </svg>
    );
  }
  if (name === 'task') {
    return (
      <svg viewBox="0 0 32 32" aria-hidden="true">
        <path d="M9 6.5h14v19H9z" />
        <path d="M12.5 10.5h7" />
        <path d="M12.5 15.5h7" />
        <path d="M12.5 20.5h4.5" />
        <path d="m20 22 2 2.2 3.8-5" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true">
      <path d="M8.5 9.5h15v10.8h-7l-4.8 4.2v-4.2H8.5z" />
      <path d="M13 14.3h.1" />
      <path d="M16 14.3h.1" />
      <path d="M19 14.3h.1" />
    </svg>
  );
}

function LeftCommandBar({
  snapshot,
  collapsed,
  onOpen,
  onToggleCollapsed,
}: {
  snapshot: SessionSnapshot;
  collapsed: boolean;
  onOpen: (overlay: OverlayPanel) => void;
  onToggleCollapsed: () => void;
}) {
  const npcCount = Object.keys(snapshot.state.npc_trust).length || snapshot.scene_npcs.length;
  const taskCount = snapshot.available_deductions.length + snapshot.available_choices.length;
  const buttons = [
    { id: 'scenes' as const, title: '场景', status: `当前 ${snapshot.scene.name}`, icon: 'scene' as const },
    { id: 'people' as const, title: '人物', status: `关键人物 ${npcCount}`, icon: 'people' as const },
    { id: 'tasks' as const, title: '任务', status: taskCount > 0 ? `进行中 ${taskCount}` : '主线推进中', icon: 'task' as const },
    { id: 'assistant' as const, title: '智能助手', status: '可询问', icon: 'assistant' as const },
  ];

  return (
    <nav className={collapsed ? 'left-command-bar collapsed' : 'left-command-bar'} aria-label="左侧功能栏">
      <button type="button" className="left-rail-toggle" onClick={onToggleCollapsed} aria-label={collapsed ? '展开左侧栏' : '收起左侧栏'}>
        {collapsed ? '展' : '收'}
      </button>
      {buttons.map((button) => (
        <button key={button.id} type="button" onClick={() => onOpen(button.id)} title={`${button.title}：${button.status}`}>
          <span className="command-icon"><CommandIcon name={button.icon} /></span>
          <strong>{button.title}</strong>
          <em>{button.status}</em>
        </button>
      ))}
    </nav>
  );
}

function SceneGridModal({ snapshot, busy, onClose, onEnterScene }: { snapshot: SessionSnapshot; busy: boolean; onClose: () => void; onEnterScene: (sceneId: string) => void }) {
  return (
    <ModalFrame title="场景" subtitle="已解锁地点" onClose={onClose}>
      <div className="scene-grid-modal">
        {snapshot.available_scenes.map((scene) => {
          const imageUrl = sceneImageUrl(scene);
          const current = scene.scene_id === snapshot.scene.scene_id;
          const hasCue = hasUndiscoveredSceneClue(scene, snapshot);
          return (
            <article key={scene.scene_id} className={current ? 'scene-grid-card current' : 'scene-grid-card'}>
              <div className="scene-grid-image">
                {imageUrl ? <img src={imageUrl} alt={`${scene.name}场景图`} /> : null}
              </div>
              <div className="scene-grid-copy">
                <div className="detail-head">
                  <strong>{scene.name}</strong>
                  <span>{current ? '当前位置' : '已解锁'}</span>
                </div>
                <p>{scene.description}</p>
                {hasCue ? <em>仍有未发现线索</em> : <em>当前线索已查过</em>}
              </div>
              <button type="button" onClick={() => onEnterScene(scene.scene_id)} disabled={busy || current}>
                {current ? '正在此处' : '前往调查'}
              </button>
            </article>
          );
        })}
      </div>
    </ModalFrame>
  );
}

function PeopleModal({ snapshot, selectedNpcId, busy, onClose, onSelectNpc }: { snapshot: SessionSnapshot; selectedNpcId: string | null; busy: boolean; onClose: () => void; onSelectNpc: (npcId: string) => void }) {
  return (
    <ModalFrame title="人物" subtitle="当前地点可盘问人物" onClose={onClose}>
      <div className="people-modal-list">
        {snapshot.scene_npcs.length > 0 ? snapshot.scene_npcs.map((npc) => {
          const npcImage = npcDisplayImage(npc);
          const trust = snapshot.state.npc_trust[npc.npc_id] ?? npc.initial_trust;
          const relatedClues = snapshot.clues.filter((clue) => clue.source_npc_id === npc.npc_id);
          const recentTurns = snapshot.dialogue_turns.filter((turn) => turn.npc_id === npc.npc_id).slice(-2);
          return (
            <article key={npc.npc_id} className={npc.npc_id === selectedNpcId ? 'person-modal-card active' : 'person-modal-card'}>
              <div className={npcImage.source === 'scene-cutout' ? 'person-portrait-frame scene-cutout' : 'person-portrait-frame'}>
                {npcImage.url ? <img src={npcImage.url} alt={`${npc.name}人物图`} /> : <span>{npc.name}</span>}
              </div>
              <div className="person-info-copy">
                <div className="detail-head">
                  <strong>{npc.name}</strong>
                  <span>信任：{getTrustLabel(trust)}（{trust}）</span>
                </div>
                <p>{npc.public_identity}</p>
                <p><b>关系：</b>{profileValue(npc, 'case_connection', snapshot)}</p>
                <p><b>已知信息：</b>{profileValue(npc, 'event_behavior', snapshot)}</p>
                <p><b>可疑点：</b>{profileValue(npc, 'background_suspicion', snapshot)}</p>
                <p><b>相关线索：</b>{relatedClues.length > 0 ? relatedClues.map((clue) => clue.title).join('、') : '尚未发现直接相关线索'}</p>
                <p><b>最近对话：</b>{recentTurns.length > 0 ? recentTurns.map((turn) => turn.npc_response).join('；') : '尚未形成对话摘要'}</p>
                <button type="button" onClick={() => onSelectNpc(npc.npc_id)} disabled={busy || npc.npc_id === selectedNpcId}>
                  {npc.npc_id === selectedNpcId ? '当前对话对象' : '切换对话对象'}
                </button>
              </div>
            </article>
          );
        }) : (
          <div className="empty-card dark-empty">当前地点暂无可盘问人物，换个场景继续查。</div>
        )}
      </div>
    </ModalFrame>
  );
}

function TaskModal({ snapshot, onClose }: { snapshot: SessionSnapshot; onClose: () => void }) {
  return (
    <ModalFrame title="任务" subtitle={snapshot.stage_label} onClose={onClose}>
      <div className="task-modal-content">
        <article>
          <strong>当前目标</strong>
          <p>{snapshot.current_goal}</p>
          <span>{stageDescriptions[snapshot.state.current_stage] ?? '继续推进调查。'}</span>
        </article>
        <article>
          <strong>可提交推理</strong>
          {snapshot.available_deductions.length > 0 ? (
            <ul>{snapshot.available_deductions.map((item) => <li key={item.deduction_id}>{item.question}</li>)}</ul>
          ) : <p>暂无可提交疑团，继续收集证据。</p>}
        </article>
        <article>
          <strong>已完成线索组合</strong>
          {snapshot.combo_summaries.length > 0 ? (
            <ul>{snapshot.combo_summaries.map((item) => <li key={item.combo_id}>{item.result_title}</li>)}</ul>
          ) : <p>暂未形成线索组合。</p>}
        </article>
      </div>
    </ModalFrame>
  );
}

function ModalFrame({ title, subtitle, children, onClose }: { title: string; subtitle: string; children: ReactNode; onClose: () => void }) {
  return (
    <div
      className="game-modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onPointerDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <section className="game-modal-panel">
        <header className="game-modal-head">
          <div>
            <p className="meta-label">{subtitle}</p>
            <h2>{title}</h2>
          </div>
          <button type="button" onClick={onClose}>关闭</button>
        </header>
        {children}
      </section>
    </div>
  );
}

export function GamePage({
  snapshot,
  selectedNpcId,
  suggestedQuestions,
  highlightClues,
  redTexts,
  actionNotice,
  debugEnabled,
  busy,
  onEnterScene,
  onInspect,
  onSelectNpc,
  onSendDialogue,
  onSubmitDeduction,
  onChoose,
  onRestart,
  onToggleDebug,
}: GamePageProps) {
  const [overlay, setOverlay] = useState<OverlayPanel>(null);
  const [investigationTab, setInvestigationTab] = useState<InvestigationTab>('clues');
  const [leftCollapsed, setLeftCollapsed] = useState(true);
  const [rightCollapsed, setRightCollapsed] = useState(true);
  const usePhaserStage = import.meta.env.VITE_USE_PHASER_STAGE !== '0';

  const stageLayer = useMemo(() => (
    usePhaserStage ? (
      <PhaserStage
        snapshot={snapshot}
        selectedNpcId={selectedNpcId}
        busy={busy}
        onSelectNpc={onSelectNpc}
        onInspect={onInspect}
      />
    ) : (
      <ScenePanel snapshot={snapshot} selectedNpcId={selectedNpcId} busy={busy} onSelectNpc={onSelectNpc} />
    )
  ), [busy, onInspect, onSelectNpc, selectedNpcId, snapshot, usePhaserStage]);

  const handleMainSurfacePointerDown = (event: ReactPointerEvent<HTMLElement>) => {
    const target = event.target;
    if (!(target instanceof Element) || target.closest(mainSurfaceIgnoreSelector)) {
      return;
    }
    if (!leftCollapsed) {
      setLeftCollapsed(true);
    }
    if (!rightCollapsed) {
      setRightCollapsed(true);
    }
  };

  if (snapshot.ending) {
    return (
      <>
        <EndingPanel ending={snapshot.ending} endingCatalog={snapshot.ending_catalog} onRestart={onRestart} />
        {debugEnabled ? <DemoEvidencePanel snapshot={snapshot} /> : null}
        {onToggleDebug ? (
          <button type="button" className="debug-toggle-button ending-debug-toggle" onClick={onToggleDebug}>
            调试
          </button>
        ) : null}
      </>
    );
  }

  return (
    <main className={[
      'visual-novel-stage main-ui-rework',
      leftCollapsed ? 'left-collapsed' : '',
      rightCollapsed ? 'right-collapsed' : '',
    ].filter(Boolean).join(' ')} onPointerDown={handleMainSurfacePointerDown}>
      {stageLayer}
      <div className="stage-dark-frame" />
      <TopStatusBar snapshot={snapshot} />
      <LeftCommandBar
        snapshot={snapshot}
        collapsed={leftCollapsed}
        onOpen={setOverlay}
        onToggleCollapsed={() => setLeftCollapsed((current) => !current)}
      />

      {debugEnabled ? <DemoEvidencePanel snapshot={snapshot} /> : null}
      {onToggleDebug ? (
        <button type="button" className="debug-toggle-button" onClick={onToggleDebug}>
          调试
        </button>
      ) : null}

      {snapshot.state.current_stage === 'choice' ? (
        <section className="choice-overlay">
          <div>
            <p className="meta-label">关键抉择</p>
            <h3>证据与活路，只能先护住一头。</h3>
          </div>
          <div className="choice-grid">
            {snapshot.available_choices.map((choice) => (
              <article key={choice.choice_id} className="choice-card">
                <h4>{choice.title}</h4>
                <p>{choice.description}</p>
                <button type="button" className="primary-button" onClick={() => onChoose(choice.choice_id)} disabled={busy}>
                  选择这一步
                </button>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <DialoguePanel
        snapshot={snapshot}
        sceneNpcs={snapshot.scene_npcs}
        dialogueTurns={snapshot.dialogue_turns}
        selectedNpcId={selectedNpcId}
        suggestedQuestions={suggestedQuestions}
        highlightClues={highlightClues ?? []}
        redTexts={redTexts}
        actionNotice={actionNotice}
        busy={busy}
        onSendDialogue={onSendDialogue}
      />

      {rightCollapsed ? (
        <button type="button" className="right-panel-rail" onClick={() => setRightCollapsed(false)} aria-label="展开右侧调查栏">
          <span>案</span>
          <strong>调查栏</strong>
        </button>
      ) : (
        <ClueSidebar
          snapshot={snapshot}
          selectedNpcId={selectedNpcId}
          busy={busy}
          activeTab={investigationTab}
          onActiveTabChange={setInvestigationTab}
          onSubmitDeduction={onSubmitDeduction}
          onCollapse={() => setRightCollapsed(true)}
        />
      )}

      {overlay === 'scenes' ? (
        <SceneGridModal snapshot={snapshot} busy={busy} onClose={() => setOverlay(null)} onEnterScene={(sceneId) => {
          setOverlay(null);
          onEnterScene(sceneId);
        }} />
      ) : null}
      {overlay === 'people' ? (
        <PeopleModal snapshot={snapshot} selectedNpcId={selectedNpcId} busy={busy} onClose={() => setOverlay(null)} onSelectNpc={(npcId) => {
          onSelectNpc(npcId);
          setOverlay(null);
        }} />
      ) : null}
      {overlay === 'tasks' ? <TaskModal snapshot={snapshot} onClose={() => setOverlay(null)} /> : null}
      {overlay === 'assistant' ? (
        <ModalFrame title="智能助手" subtitle="后端安全调用" onClose={() => setOverlay(null)}>
          <AssistantPanel snapshot={snapshot} />
        </ModalFrame>
      ) : null}
    </main>
  );
}

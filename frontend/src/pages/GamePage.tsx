import { ClueSidebar } from '../components/clue/ClueSidebar';
import { DialoguePanel } from '../components/dialogue/DialoguePanel';
import { DemoEvidencePanel } from '../components/debug/DemoEvidencePanel';
import { EndingPanel } from '../components/ending/EndingPanel';
import { ScenePanel } from '../components/scene/ScenePanel';
import type { SessionSnapshot } from '../types/game';

type GamePageProps = {
  snapshot: SessionSnapshot;
  selectedNpcId: string | null;
  suggestedQuestions: string[];
  highlightClues: SessionSnapshot['dialogue_turns'][number]['highlight_clues'];
  redTexts: string[];
  actionNotice: string;
  presentationFeedback: string[];
  debugEnabled: boolean;
  busy: boolean;
  onEnterScene: (sceneId: string) => void;
  onInspect: (sceneId: string, hotspotId: string, clueId?: string | null) => void;
  onSelectNpc: (npcId: string) => void;
  onSendDialogue: (npcId: string, message: string, presentedClueIds: string[]) => void;
  onSubmitDeduction: (deductionId: string, selectedClueIds: string[]) => void;
  onChoose: (choiceId: string) => void;
  onRestart: () => void;
  onToggleDebug?: () => void;
};

export function GamePage({
  snapshot,
  selectedNpcId,
  suggestedQuestions,
  highlightClues,
  redTexts,
  actionNotice,
  presentationFeedback,
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
    <main className="visual-novel-stage">
      <ScenePanel snapshot={snapshot} selectedNpcId={selectedNpcId} busy={busy} onSelectNpc={onSelectNpc} />
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
        presentationFeedback={presentationFeedback}
        busy={busy}
        onSendDialogue={onSendDialogue}
      />

      <ClueSidebar
        snapshot={snapshot}
        selectedNpcId={selectedNpcId}
        busy={busy}
        onEnterScene={onEnterScene}
        onInspect={onInspect}
        onSelectNpc={onSelectNpc}
        onSubmitDeduction={onSubmitDeduction}
      />
    </main>
  );
}

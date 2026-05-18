import { useEffect, useMemo, useState } from 'react';

import { api } from './api/client';
import {
  buildScenarioPreview,
  getFallbackDynasties,
  getFallbackIdentityRecommendations,
  getFallbackRoleForDynasty,
  type GeneratedScenarioPreview,
} from './mock/entryFlow';
import { GamePage } from './pages/GamePage';
import { ScenarioGenerationPage } from './pages/ScenarioGenerationPage';
import { StartPage } from './pages/StartPage';
import { buildActionNotice } from './store/gameStore';
import type { DialogueActionResult, DialogueHighlight, Dynasty, GameState, HealthResponse, PlayerRole, SessionSnapshot } from './types/game';

const debugStorageKey = 'historyGameDebug';
const debugUiAllowed = import.meta.env.DEV && import.meta.env.VITE_SHOW_DEBUG_PANEL === '1';

function getInitialDebugEnabled(): boolean {
  if (!debugUiAllowed || typeof window === 'undefined') {
    return false;
  }

  const params = new URLSearchParams(window.location.search);
  if (params.get('debug') === '1') {
    return true;
  }

  try {
    return window.localStorage.getItem(debugStorageKey) === '1';
  } catch {
    return false;
  }
}

function diffNumber(current: number, next: number): number {
  return next - current;
}

function buildScoreFeedback(before: GameState, after: GameState): string[] {
  const scoreLabels: Record<keyof GameState['scores'], string> = {
    truth: '真相',
    order: '秩序',
    survival: '自保',
    sacrifice: '牺牲',
  };

  return (Object.keys(scoreLabels) as Array<keyof GameState['scores']>)
    .map((scoreKey) => {
      const delta = diffNumber(before.scores[scoreKey], after.scores[scoreKey]);
      return delta === 0 ? '' : `${scoreLabels[scoreKey]}${delta > 0 ? '+' : ''}${delta}`;
    })
    .filter(Boolean);
}

function buildPresentationFeedback(
  beforeSnapshot: SessionSnapshot,
  result: DialogueActionResult,
  npcId: string,
  presentedClueIds: string[],
): string[] {
  if (presentedClueIds.length === 0) {
    return [];
  }

  const clueTitleMap = new Map(beforeSnapshot.clues.map((clue) => [clue.clue_id, clue.title]));
  const beforeState = beforeSnapshot.state;
  const afterState = result.state;
  const presentedTitles = presentedClueIds.map((clueId) => clueTitleMap.get(clueId) ?? clueId);
  const feedback = [`已出示：${presentedTitles.join('、')}`];

  const trustDelta = diffNumber(beforeState.npc_trust[npcId] ?? 0, afterState.npc_trust[npcId] ?? 0);
  if (trustDelta !== 0) {
    feedback.push(`${result.dialogue.npc_name}信任${trustDelta > 0 ? '+' : ''}${trustDelta}`);
  }

  const scoreFeedback = buildScoreFeedback(beforeState, afterState);
  if (scoreFeedback.length > 0) {
    feedback.push(scoreFeedback.join('，'));
  }

  const riskDelta = diffNumber(beforeState.risk_level, afterState.risk_level);
  if (riskDelta !== 0) {
    feedback.push(`风险${riskDelta > 0 ? '+' : ''}${riskDelta}`);
  }

  const newFlags = afterState.flags.filter((flag) => !beforeState.flags.includes(flag));
  if (newFlags.length > 0) {
    feedback.push('状态更新');
  }

  if (result.new_clues.length > 0) {
    feedback.push(`案卷新增：${result.new_clues.map((clue) => clue.title).join('、')}`);
  }
  if (result.new_combos.length > 0) {
    feedback.push(`线索组合：${result.new_combos.map((combo) => combo.result_title).join('、')}`);
  }
  if (result.new_deductions.length > 0) {
    feedback.push(`新疑团：${result.new_deductions.map((deduction) => deduction.question).join('、')}`);
  }

  if (feedback.length === 1) {
    feedback.push(`${result.dialogue.npc_name}对证据作出回应，但案卷状态暂未新增。`);
  }

  return feedback;
}

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [dynasties, setDynasties] = useState<Dynasty[]>([]);
  const [selectedDynastyId, setSelectedDynastyId] = useState('');
  const [generatedScenario, setGeneratedScenario] = useState<GeneratedScenarioPreview | null>(null);
  const [snapshot, setSnapshot] = useState<SessionSnapshot | null>(null);
  const [selectedNpcId, setSelectedNpcId] = useState<string | null>(null);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [dialogueHighlights, setDialogueHighlights] = useState<DialogueHighlight[]>([]);
  const [dialogueRedTexts, setDialogueRedTexts] = useState<string[]>([]);
  const [actionNotice, setActionNotice] = useState('书页尚未翻开。');
  const [presentationFeedback, setPresentationFeedback] = useState<string[]>([]);
  const [debugEnabled, setDebugEnabled] = useState(getInitialDebugEnabled);
  const [errorText, setErrorText] = useState('');
  const [loadingBoot, setLoadingBoot] = useState(true);
  const [busy, setBusy] = useState(false);

  const backendReady = health?.status === 'ok';

  const loadBootData = async (options?: { showSplash?: boolean }) => {
    const showSplash = options?.showSplash ?? true;
    if (showSplash) {
      setLoadingBoot(true);
    }
    setErrorText('');
    try {
      const [healthResult, dynastyResult] = await Promise.allSettled([api.getHealth(), api.getDynasties()]);

      const nextHealth = healthResult.status === 'fulfilled' ? healthResult.value : null;
      const nextDynasties = dynastyResult.status === 'fulfilled' && dynastyResult.value.dynasties.length > 0
        ? dynastyResult.value.dynasties
        : getFallbackDynasties();

      setHealth(nextHealth);
      setDynasties(nextDynasties);
      setActionNotice(nextHealth ? '朝代入口已就绪，等待生成第一桩案。' : '后端未连通，已切换到离线展示模式。');
    } catch {
      setHealth(null);
      setDynasties(getFallbackDynasties());
      setActionNotice('后端未连通，已切换到离线展示模式。');
    } finally {
      if (showSplash) {
        setLoadingBoot(false);
      }
    }
  };

  const syncSession = async (sessionId: string, preferredNpcId?: string | null) => {
    const nextSnapshot = await api.getSession(sessionId);
    setSnapshot(nextSnapshot);
    const sceneNpcIds = nextSnapshot.scene_npcs.map((npc) => npc.npc_id);
    const nextNpcId = preferredNpcId && sceneNpcIds.includes(preferredNpcId)
      ? preferredNpcId
      : sceneNpcIds[0] ?? null;
    setSelectedNpcId(nextNpcId);
    return nextSnapshot;
  };

  useEffect(() => {
    void loadBootData();
  }, []);

  const selectedDynasty = useMemo(
    () => dynasties.find((item) => item.dynasty_id === selectedDynastyId) ?? null,
    [dynasties, selectedDynastyId],
  );

  const handleSelectDynasty = (dynastyId: string) => {
    setSelectedDynastyId(dynastyId);
    setGeneratedScenario(null);
    setPresentationFeedback([]);
    setDialogueHighlights([]);
    setDialogueRedTexts([]);
    setErrorText('');
  };

  const resolveRoleForDynasty = async (dynasty: Dynasty): Promise<PlayerRole> => {
    try {
      const roleResponse = await api.getRoles(dynasty.dynasty_id);
      const enabledRole = roleResponse.roles.find((role) => role.enabled);
      if (enabledRole) {
        return enabledRole;
      }
    } catch {
      // 使用本地兜底身份，确保离线时仍可演示前两步流程。
    }

    const fallbackRole = getFallbackRoleForDynasty(dynasty.dynasty_id);
    if (!fallbackRole) {
      throw new Error('当前朝代暂无可用身份，无法生成本局事件。');
    }
    return fallbackRole;
  };

  const handlePrepareScenario = async () => {
    if (!selectedDynasty) {
      setErrorText('请先选择一个朝代。');
      return;
    }
    if (!selectedDynasty.enabled) {
      setErrorText('该朝代的完整可玩链路尚未开放，请先体验当前已开放的朝代。');
      return;
    }

    setBusy(true);
    setErrorText('');
    try {
      const role = await resolveRoleForDynasty(selectedDynasty);
      const basePreview = buildScenarioPreview(selectedDynasty, role);
      let identityRecommendations = getFallbackIdentityRecommendations();
      if (backendReady) {
        try {
          identityRecommendations = await api.getPlayerIdentities({
            dynasty_id: selectedDynasty.dynasty_id,
            event_id: basePreview.eventId,
          });
        } catch {
          identityRecommendations = getFallbackIdentityRecommendations();
        }
      }
      setGeneratedScenario(buildScenarioPreview(selectedDynasty, role, identityRecommendations));
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : '生成本局事件失败，请稍后重试。');
    } finally {
      setBusy(false);
    }
  };

  const handleRefreshBackend = async () => {
    setBusy(true);
    try {
      await loadBootData({ showSplash: false });
    } finally {
      setBusy(false);
    }
  };

  const handleStart = async (identityPayload?: { identity_id?: string; custom_identity_text?: string }) => {
    if (!generatedScenario) {
      setErrorText('请先完成本局事件生成。');
      return;
    }
    if (!backendReady) {
      setErrorText('当前仍处于离线展示模式。请先启动后端服务，再进入正式剧情。');
      return;
    }

    setBusy(true);
    setErrorText('');
    try {
      const nextSnapshot = await api.startSession({
        dynasty_id: generatedScenario.dynastyId,
        role_id: generatedScenario.roleId,
        event_id: generatedScenario.eventId,
        ...identityPayload,
      });

      setSnapshot(nextSnapshot);
      setSelectedNpcId(nextSnapshot.scene_npcs[0]?.npc_id ?? null);
      setSuggestedQuestions(['昨夜第一眼看见什么？', '谁最先靠近过旧书箱？', '火场最不对劲的痕迹在哪里？']);
      setDialogueHighlights([]);
      setDialogueRedTexts([]);
      setPresentationFeedback([]);
      setActionNotice(nextSnapshot.player_identity?.background ?? '本局事件已经展开，你正站在第一幕的雨声里。');
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : '开局失败，请稍后重试。');
    } finally {
      setBusy(false);
    }
  };

  const handleEnterScene = async (sceneId: string) => {
    if (!snapshot) {
      return;
    }
    setBusy(true);
    setErrorText('');
    try {
      const result = await api.investigate({
        session_id: snapshot.session_id,
        scene_id: sceneId,
      });
      setPresentationFeedback([]);
      setDialogueHighlights([]);
      setDialogueRedTexts([]);
      setActionNotice(result.text);
      await syncSession(snapshot.session_id);
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : '场景切换失败。');
    } finally {
      setBusy(false);
    }
  };

  const handleInspect = async (sceneId: string, hotspotId: string, clueId?: string | null) => {
    if (!snapshot) {
      return;
    }
    setBusy(true);
    setErrorText('');
    try {
      const result = await api.investigate({
        session_id: snapshot.session_id,
        scene_id: sceneId,
        hotspot_id: hotspotId,
        clue_id: clueId,
      });
      setPresentationFeedback([]);
      setDialogueHighlights([]);
      setDialogueRedTexts([]);
      setActionNotice(buildActionNotice(result.text, [
        ...result.new_clues.map((clue) => clue.title),
        ...result.new_combos.map((combo) => combo.result_title),
        ...result.new_deductions.map((deduction) => deduction.question),
      ]));
      await syncSession(snapshot.session_id, selectedNpcId);
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : '调查失败。');
    } finally {
      setBusy(false);
    }
  };

  const handleSendDialogue = async (npcId: string, message: string, presentedClueIds: string[]) => {
    if (!snapshot) {
      return;
    }
    setBusy(true);
    setErrorText('');
    try {
      const result = await api.dialogue({
        session_id: snapshot.session_id,
        npc_id: npcId,
        message,
        action_type: presentedClueIds.length > 0 ? 'present_clue' : 'question',
        presented_clue_ids: presentedClueIds,
      });
      setSuggestedQuestions(result.dialogue.suggested_questions);
      setDialogueHighlights(result.dialogue.highlight_clues ?? []);
      setDialogueRedTexts(result.dialogue.red_texts ?? []);
      setPresentationFeedback(buildPresentationFeedback(snapshot, result, npcId, presentedClueIds));
      setActionNotice(buildActionNotice(`${result.dialogue.npc_name}：${result.dialogue.npc_dialogue}`, [
        ...result.new_clues.map((clue) => clue.title),
        ...result.new_combos.map((combo) => combo.result_title),
        ...result.new_deductions.map((deduction) => deduction.question),
      ]));
      await syncSession(snapshot.session_id, npcId);
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : '对话失败。');
    } finally {
      setBusy(false);
    }
  };

  const handleSubmitDeduction = async (deductionId: string, selectedClueIds: string[]) => {
    if (!snapshot) {
      return;
    }
    setBusy(true);
    setErrorText('');
    try {
      const result = await api.submitDeduction({
        session_id: snapshot.session_id,
        deduction_id: deductionId,
        selected_clue_ids: selectedClueIds,
      });
      setPresentationFeedback([]);
      setDialogueHighlights([]);
      setDialogueRedTexts([]);
      setActionNotice(result.correct ? `推理成立：${result.feedback}` : `推理未成立：${result.feedback}`);
      await syncSession(snapshot.session_id, selectedNpcId);
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : '提交推理失败。');
    } finally {
      setBusy(false);
    }
  };

  const handleChoose = async (choiceId: string) => {
    if (!snapshot) {
      return;
    }
    setBusy(true);
    setErrorText('');
    try {
      await api.choose({
        session_id: snapshot.session_id,
        choice_id: choiceId,
      });
      const ending = await api.resolveEnding({ session_id: snapshot.session_id });
      setSuggestedQuestions([]);
      setDialogueHighlights([]);
      setDialogueRedTexts([]);
      setPresentationFeedback([]);
      setActionNotice(`你做出了最终抉择，结局“${ending.title}”已经落定。`);
      await syncSession(snapshot.session_id);
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : '提交抉择失败。');
    } finally {
      setBusy(false);
    }
  };

  const handleRestart = () => {
    setSnapshot(null);
    setGeneratedScenario(null);
    setSelectedDynastyId('');
    setSelectedNpcId(null);
    setSuggestedQuestions([]);
    setDialogueHighlights([]);
    setDialogueRedTexts([]);
    setPresentationFeedback([]);
    setActionNotice('回到卷首，准备重新选择朝代。');
    setErrorText('');
  };

  const handleToggleDebug = () => {
    setDebugEnabled((current) => {
      const next = !current;
      try {
        window.localStorage.setItem(debugStorageKey, next ? '1' : '0');
      } catch {
        // 调试开关仅影响本地显示；localStorage 不可用时仍允许本次切换。
      }
      return next;
    });
  };

  if (loadingBoot) {
    return <div className="screen-center">正在连接史隙引擎……</div>;
  }

  return (
    <div className="app-frame">
      {snapshot ? (
        <>
          {errorText ? <div className="error-banner floating">{errorText}</div> : null}
          <GamePage
            snapshot={snapshot}
            selectedNpcId={selectedNpcId}
            suggestedQuestions={suggestedQuestions}
            highlightClues={dialogueHighlights}
            redTexts={dialogueRedTexts}
            actionNotice={actionNotice}
            presentationFeedback={presentationFeedback}
            debugEnabled={debugUiAllowed && debugEnabled}
            busy={busy}
            onEnterScene={handleEnterScene}
            onInspect={handleInspect}
            onSelectNpc={setSelectedNpcId}
            onSendDialogue={handleSendDialogue}
            onSubmitDeduction={handleSubmitDeduction}
            onChoose={handleChoose}
            onRestart={handleRestart}
            onToggleDebug={debugUiAllowed ? handleToggleDebug : undefined}
          />
        </>
      ) : generatedScenario ? (
        <ScenarioGenerationPage
          health={health}
          backendReady={backendReady}
          preview={generatedScenario}
          busy={busy}
          errorText={errorText}
          onBack={() => {
            setGeneratedScenario(null);
            setErrorText('');
          }}
          onRefreshBackend={() => {
            void handleRefreshBackend();
          }}
          onEnterEvent={(identityPayload) => {
            void handleStart(identityPayload);
          }}
        />
      ) : (
        <StartPage
          health={health}
          backendReady={backendReady}
          dynasties={dynasties}
          selectedDynastyId={selectedDynastyId}
          busy={busy}
          errorText={errorText}
          onSelectDynasty={handleSelectDynasty}
          onRefreshBackend={() => {
            void handleRefreshBackend();
          }}
          onPrepareScenario={() => {
            void handlePrepareScenario();
          }}
        />
      )}
    </div>
  );
}

export default App;

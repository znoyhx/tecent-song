import { useEffect, useMemo, useState } from 'react';

import { api } from './api/client';
import { AudioDirector } from './components/audio/AudioDirector';
import { FixedDemoOverviewPage, ScriptOverviewPage, ScriptProgressPage } from './components/script-generation/ScriptGenerationFlow';
import { GamePage } from './pages/GamePage';
import { StartPage } from './pages/StartPage';
import type {
  DialogueHighlight,
  DialogueMessageSource,
  Dynasty,
  GeneratedScriptDemo,
  HealthResponse,
  PlayerIdentityRecommendations,
  ScriptJob,
  ScriptPackage,
  SessionSnapshot,
} from './types/game';

const debugStorageKey = 'historyGameDebug';
const debugUiAllowed = import.meta.env.DEV && import.meta.env.VITE_SHOW_DEBUG_PANEL === '1';
const mingRuntimePayload = {
  dynasty_id: 'ming',
  role_id: 'role_ming_bookshop_apprentice',
  event_id: 'ming_bookshop_fire',
};

type EntryMode = 'home' | 'setup' | 'fixedOverview' | 'progress' | 'overview';

const fallbackDynasties: Dynasty[] = [
  {
    dynasty_id: 'ming',
    name: '明代',
    enabled: true,
    period_label: '书坊焚稿案',
    core_mood: '固定 Demo',
    allowed_roles: ['书坊学徒'],
    forbidden_terms: [],
    visual_keywords: [],
  },
  {
    dynasty_id: 'song',
    name: '北宋',
    enabled: true,
    period_label: 'AI 剧本生成',
    core_mood: '关键词生成案件',
    allowed_roles: [],
    forbidden_terms: [],
    visual_keywords: [],
  },
  {
    dynasty_id: 'tang',
    name: '晚唐',
    enabled: true,
    period_label: 'AI 剧本生成',
    core_mood: '关键词生成案件',
    allowed_roles: [],
    forbidden_terms: [],
    visual_keywords: [],
  },
];

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

function parseKeywords(value: string): string[] {
  return value
    .replace(/\n/g, '、')
    .replace(/,/g, '、')
    .replace(/，/g, '、')
    .split('、')
    .map((item) => item.trim())
    .filter(Boolean);
}

function hasVagueKeyword(keywords: string[]): boolean {
  const vague = new Set(['好玩', '刺激', '随便', '有趣', '悬疑', '故事']);
  return keywords.some((keyword) => vague.has(keyword));
}

function generatedDynastyId(dynastyId: string): 'song' | 'late_tang' | 'ming' | 'tang' {
  return dynastyId === 'tang' ? 'late_tang' : (dynastyId as 'song' | 'late_tang' | 'ming' | 'tang');
}

function App() {
  const [entryMode, setEntryMode] = useState<EntryMode>('home');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [dynasties, setDynasties] = useState<Dynasty[]>(fallbackDynasties);
  const [selectedDynastyId, setSelectedDynastyId] = useState('');
  const [keywordText, setKeywordText] = useState('');
  const [scriptJob, setScriptJob] = useState<ScriptJob | null>(null);
  const [scriptPackage, setScriptPackage] = useState<ScriptPackage | null>(null);
  const [savedDemos, setSavedDemos] = useState<GeneratedScriptDemo[]>([]);
  const [savedDemosLoaded, setSavedDemosLoaded] = useState(false);
  const [savedDemosError, setSavedDemosError] = useState('');
  const [fixedIdentityRecommendations, setFixedIdentityRecommendations] = useState<PlayerIdentityRecommendations | null>(null);
  const [snapshot, setSnapshot] = useState<SessionSnapshot | null>(null);
  const [selectedNpcId, setSelectedNpcId] = useState<string | null>(null);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [dialogueHighlights, setDialogueHighlights] = useState<DialogueHighlight[]>([]);
  const [dialogueRedTexts, setDialogueRedTexts] = useState<string[]>([]);
  const [actionNotice, setActionNotice] = useState('选择朝代后开始调查。');
  const [debugEnabled, setDebugEnabled] = useState(getInitialDebugEnabled);
  const [errorText, setErrorText] = useState('');
  const [loadingBoot, setLoadingBoot] = useState(true);
  const [busy, setBusy] = useState(false);

  const selectedDynasty = useMemo(
    () => dynasties.find((item) => item.dynasty_id === selectedDynastyId) ?? null,
    [dynasties, selectedDynastyId],
  );

  const loadSavedDemos = async () => {
    setSavedDemosError('');
    try {
      const result = await api.listGeneratedDemos();
      setSavedDemos(result.demos);
    } catch {
      setSavedDemos([]);
      setSavedDemosError('已生成 Demo 暂时无法读取');
    } finally {
      setSavedDemosLoaded(true);
    }
  };

  useEffect(() => {
    const loadBootData = async () => {
      setLoadingBoot(true);
      setSavedDemosError('');
      try {
        const [healthResult, dynastyResult, demoResult] = await Promise.allSettled([
          api.getHealth(),
          api.getDynasties(),
          api.listGeneratedDemos(),
        ]);
        setHealth(healthResult.status === 'fulfilled' ? healthResult.value : null);
        if (dynastyResult.status === 'fulfilled' && dynastyResult.value.dynasties.length > 0) {
          const backendDynasties = dynastyResult.value.dynasties;
          const hasTang = backendDynasties.some((item) => item.dynasty_id === 'tang' || item.dynasty_id === 'late_tang');
          setDynasties(hasTang ? backendDynasties : [...backendDynasties, fallbackDynasties[2]]);
        }
        if (demoResult.status === 'fulfilled') {
          setSavedDemos(demoResult.value.demos);
        } else {
          setSavedDemos([]);
          setSavedDemosError('已生成 Demo 暂时无法读取');
        }
      } finally {
        setSavedDemosLoaded(true);
        setLoadingBoot(false);
      }
    };
    void loadBootData();
  }, []);

  useEffect(() => {
    if (entryMode !== 'progress' || !scriptJob || ['completed', 'failed', 'visual_blocked'].includes(scriptJob.status)) {
      return undefined;
    }
    const timer = window.setInterval(async () => {
      try {
        const latest = await api.getScriptJob(scriptJob.job_id);
        setScriptJob(latest);
      } catch (error) {
        setErrorText(error instanceof Error ? error.message : '读取生成任务失败。');
      }
    }, 2000);
    return () => window.clearInterval(timer);
  }, [entryMode, scriptJob]);

  useEffect(() => {
    if (!scriptJob || scriptJob.status !== 'completed' || !scriptJob.ready_for_overview || !scriptJob.script_id) {
      return;
    }
    void openOverview(scriptJob);
  }, [scriptJob?.status, scriptJob?.ready_for_overview, scriptJob?.script_id]);

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

  const startMingDemo = async (identityId?: string, customIdentityText?: string) => {
    setBusy(true);
    setErrorText('');
    try {
      const nextSnapshot = await api.startSession({
        ...mingRuntimePayload,
        ...(customIdentityText ? { custom_identity_text: customIdentityText } : identityId ? { identity_id: identityId } : {}),
      });
      setSnapshot(nextSnapshot);
      setSelectedNpcId(nextSnapshot.scene_npcs[0]?.npc_id ?? null);
      setSuggestedQuestions(['昨夜谁先到火场？', '这条线索能说明什么？', '还有谁接触过旧书箱？']);
      setActionNotice('明代固定 Demo 已启动。');
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : '明代 Demo 启动失败。');
    } finally {
      setBusy(false);
    }
  };

  const handleGenerateScript = async (targetDynasty = selectedDynasty) => {
    if (!targetDynasty || targetDynasty.dynasty_id === 'ming') {
      setErrorText('请先选择北宋或晚唐。');
      return;
    }
    const keywords = parseKeywords(keywordText);
    if (keywords.length === 0) {
      setErrorText('请至少填写 1 个关键词。');
      return;
    }
    if (keywords.length > 8) {
      setErrorText('关键词最多 8 个，请删减后重试。');
      return;
    }
    if (hasVagueKeyword(keywords)) {
      setErrorText('关键词过于空泛，请补充地点、人物关系、器物或冲突。');
      return;
    }
    setBusy(true);
    setErrorText('');
    try {
      const job = await api.generateScript({ dynasty_id: generatedDynastyId(targetDynasty.dynasty_id), keywords });
      setScriptJob(job);
      setScriptPackage(null);
      setEntryMode('progress');
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : '剧本生成请求失败。');
    } finally {
      setBusy(false);
    }
  };

  const handlePrepareScenario = async () => {
    const defaultDynastyId = dynasties.find((item) => item.enabled)?.dynasty_id ?? 'ming';
    const targetDynastyId = selectedDynastyId || defaultDynastyId;
    const targetDynasty = dynasties.find((item) => item.dynasty_id === targetDynastyId) ?? fallbackDynasties[0];
    setSelectedDynastyId(targetDynasty.dynasty_id);
    setErrorText('');
    if (targetDynasty.dynasty_id === 'ming') {
      setBusy(true);
      try {
        const recommendations = await api.getPlayerIdentities({ dynasty_id: 'ming', event_id: mingRuntimePayload.event_id });
        setFixedIdentityRecommendations(recommendations);
        setEntryMode('fixedOverview');
      } catch (error) {
        setErrorText(error instanceof Error ? error.message : '读取明代身份与概览失败。');
      } finally {
        setBusy(false);
      }
      return;
    }
    void handleGenerateScript(targetDynasty);
  };

  const openOverview = async (job = scriptJob) => {
    if (!job || job.status !== 'completed' || !job.ready_for_overview || !job.script_id) {
      setErrorText('后端 job 尚未完成，不能进入剧本概览。');
      return;
    }
    setBusy(true);
    setErrorText('');
    try {
      const script = await api.getScript(job.script_id);
      setScriptPackage(script);
      setEntryMode('overview');
      void loadSavedDemos();
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : '读取剧本概览失败。');
    } finally {
      setBusy(false);
    }
  };

  const completedDemoJob = (script: ScriptPackage): ScriptJob => {
    const approved = (assetType: 'scene' | 'npc' | 'clue') =>
      script.visual_assets.filter((asset) => asset.asset_type === assetType && asset.quality_gate.status === 'approved').length;
    const sceneApproved = approved('scene');
    const npcApproved = approved('npc');
    const clueApproved = approved('clue');

    return {
      job_id: `saved_${script.script_id}`,
      dynasty_id: script.dynasty_id,
      keywords: script.keywords,
      status: 'completed',
      progress: 100,
      current_step: 'completed',
      steps: [],
      blocking_issues: [],
      transitional_quote: null,
      visual_quality: {
        scene: { approved: sceneApproved, required: Math.max(8, sceneApproved) },
        npc: { approved: npcApproved, required: Math.max(4, npcApproved) },
        clue: { approved: clueApproved, required: Math.max(6, clueApproved) },
      },
      ready_for_overview: true,
      script_id: script.script_id,
    };
  };

  const handleOpenSavedDemo = async (scriptId: string) => {
    setBusy(true);
    setErrorText('');
    try {
      const script = await api.getScript(scriptId);
      setScriptPackage(script);
      setScriptJob(completedDemoJob(script));
      setSelectedDynastyId(script.dynasty_id);
      setEntryMode('overview');
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : '读取已保存 Demo 失败。');
    } finally {
      setBusy(false);
    }
  };

  const handleStartGenerated = async (identityPayload: { identity_id?: string; custom_identity_text?: string }) => {
    if (!scriptPackage) {
      setErrorText('生成剧本尚未载入。');
      return;
    }
    setBusy(true);
    setErrorText('');
    try {
      const nextSnapshot = await api.startGeneratedSession({ script_id: scriptPackage.script_id, ...identityPayload });
      setSnapshot(nextSnapshot);
      setSelectedNpcId(nextSnapshot.scene_npcs[0]?.npc_id ?? null);
      setSuggestedQuestions(['你当时看见了什么？', '这件物证是谁留下的？', '还有谁知道这件事？']);
      setDialogueHighlights([]);
      setDialogueRedTexts([]);
      setActionNotice('生成剧本已进入首场景。');
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : '进入生成剧本失败。');
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
      const result = await api.investigate({ session_id: snapshot.session_id, scene_id: sceneId });
      setDialogueHighlights([]);
      setDialogueRedTexts([]);
      setActionNotice(result.text);
      await syncSession(snapshot.session_id);
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : '进入场景失败。');
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
      const result = await api.investigate({ session_id: snapshot.session_id, scene_id: sceneId, hotspot_id: hotspotId, clue_id: clueId });
      const discoveries = [...result.new_clues.map((clue) => clue.title), ...result.new_combos.map((combo) => combo.result_title)];
      setDialogueHighlights([]);
      setDialogueRedTexts([]);
      setActionNotice(discoveries.length > 0 ? `${result.text}\n新发现：${discoveries.join('、')}` : result.text);
      await syncSession(snapshot.session_id, selectedNpcId);
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : '调查失败。');
    } finally {
      setBusy(false);
    }
  };

  const handleSendDialogue = async (npcId: string, message: string, presentedClueIds: string[], messageSource: DialogueMessageSource) => {
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
        action_type: messageSource === 'suggested_option' ? 'suggested_question' : (presentedClueIds.length > 0 ? 'present_clue' : 'question'),
        message_source: messageSource,
        presented_clue_ids: presentedClueIds,
      });
      setSuggestedQuestions(result.dialogue.suggested_questions);
      setDialogueHighlights(result.dialogue.highlight_clues ?? []);
      setDialogueRedTexts(result.dialogue.red_texts ?? []);
      const discoveries = [...result.new_clues.map((clue) => clue.title), ...result.new_combos.map((combo) => combo.result_title)];
      setActionNotice(discoveries.length > 0 ? `${result.dialogue.npc_name}：${result.dialogue.npc_dialogue}\n新发现：${discoveries.join('、')}` : `${result.dialogue.npc_name}：${result.dialogue.npc_dialogue}`);
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
      const result = await api.submitDeduction({ session_id: snapshot.session_id, deduction_id: deductionId, selected_clue_ids: selectedClueIds });
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
      await api.choose({ session_id: snapshot.session_id, choice_id: choiceId });
      const ending = await api.resolveEnding({ session_id: snapshot.session_id });
      setSuggestedQuestions([]);
      setDialogueHighlights([]);
      setDialogueRedTexts([]);
      setActionNotice(`结局判定：${ending.title}`);
      await syncSession(snapshot.session_id);
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : '提交抉择失败。');
    } finally {
      setBusy(false);
    }
  };

  const handleRestart = () => {
    setSnapshot(null);
    setScriptJob(null);
    setScriptPackage(null);
    setFixedIdentityRecommendations(null);
    setSelectedDynastyId('');
    setKeywordText('');
    setEntryMode('home');
    setSelectedNpcId(null);
    setSuggestedQuestions([]);
    setDialogueHighlights([]);
    setDialogueRedTexts([]);
    setActionNotice('选择朝代后开始调查。');
    setErrorText('');
  };

  const handleToggleDebug = () => {
    setDebugEnabled((current) => {
      const next = !current;
      try {
        window.localStorage.setItem(debugStorageKey, next ? '1' : '0');
      } catch {
        // localStorage unavailable.
      }
      return next;
    });
  };

  if (loadingBoot) {
    return <div className="screen-center">正在连接后端...</div>;
  }

  return (
    <div className="app-frame">
      <AudioDirector snapshot={snapshot} selectedNpcId={selectedNpcId} />
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
      ) : entryMode === 'fixedOverview' && fixedIdentityRecommendations ? (
        <FixedDemoOverviewPage
          identities={fixedIdentityRecommendations}
          busy={busy}
          errorText={errorText}
          onBack={() => setEntryMode('setup')}
          onStart={(payload) => void startMingDemo(payload.identity_id, payload.custom_identity_text)}
        />
      ) : entryMode === 'progress' && scriptJob ? (
        <ScriptProgressPage
          job={scriptJob}
          errorText={errorText}
          onBack={handleRestart}
          onOpenOverview={() => void openOverview()}
        />
      ) : entryMode === 'overview' && scriptJob && scriptPackage ? (
        <ScriptOverviewPage
          job={scriptJob}
          script={scriptPackage}
          busy={busy}
          errorText={errorText}
          onBack={() => setEntryMode(scriptJob.job_id.startsWith('saved_') ? 'setup' : 'progress')}
          onStart={handleStartGenerated}
        />
      ) : (
        <StartPage
          mode={entryMode === 'home' ? 'home' : 'setup'}
          dynasties={dynasties}
          selectedDynastyId={selectedDynastyId}
          keywordText={keywordText}
          busy={busy}
          errorText={errorText}
          savedDemos={savedDemos}
          savedDemosLoaded={savedDemosLoaded}
          savedDemosError={savedDemosError}
          onStart={() => {
            setSelectedDynastyId((current) => current || dynasties.find((item) => item.enabled)?.dynasty_id || 'ming');
            setEntryMode('setup');
            setErrorText('');
          }}
          onSelectDynasty={(dynastyId) => {
            setSelectedDynastyId(dynastyId);
            setErrorText('');
          }}
          onKeywordTextChange={setKeywordText}
          onPrepareScenario={handlePrepareScenario}
          onOpenSavedDemo={(scriptId) => void handleOpenSavedDemo(scriptId)}
        />
      )}
      {!health ? <span className="sr-only">后端状态未知，部分功能可能不可用。</span> : null}
    </div>
  );
}

export default App;

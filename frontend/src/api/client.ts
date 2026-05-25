import type {
  ChoiceCard,
  DeductionSubmitResult,
  DialogueActionResult,
  DialogueMessageSource,
  Dynasty,
  EndingResult,
  HealthResponse,
  InvestigateActionResult,
  PlayerIdentityRecommendations,
  PlayerIdentityValidationResult,
  PlayerRole,
  GeneratedScriptDemo,
  ScriptJob,
  ScriptPackage,
  SessionSnapshot,
} from '../types/game';

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

function buildApiUrl(path: string): string {
  return API_BASE ? `${API_BASE}${path}` : path;
}

export function resolveApiUrl(path?: string | null, fallbackPath = ''): string {
  const target = path || fallbackPath;
  if (!target) {
    return '';
  }
  return target.startsWith('http') ? target : buildApiUrl(target);
}

export function visualAssetUrl(assetId: string): string {
  return buildApiUrl(`/api/visual/assets/${assetId}`);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  const headers = new Headers(init?.headers);

  if (init?.body != null && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  try {
    response = await fetch(buildApiUrl(path), { ...init, headers });
  } catch {
    throw new Error('无法连接后端服务，请确认服务已启动。');
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.error?.message ?? '请求失败，请稍后重试。';
    throw new Error(message);
  }
  return data as T;
}

export const api = {
  getHealth() {
    return request<HealthResponse>('/api/health');
  },
  getDynasties() {
    return request<{ dynasties: Dynasty[] }>('/api/dynasties');
  },
  getRoles(dynastyId: string) {
    return request<{ roles: PlayerRole[] }>(`/api/roles?dynasty_id=${dynastyId}`);
  },
  getPlayerIdentities(payload: { dynasty_id: string; event_id: string }) {
    const params = new URLSearchParams({ dynasty_id: payload.dynasty_id, event_id: payload.event_id });
    return request<PlayerIdentityRecommendations>(`/api/player-identities?${params.toString()}`);
  },
  validatePlayerIdentity(payload: { dynasty_id: string; event_id: string; custom_identity_text: string }) {
    return request<PlayerIdentityValidationResult>('/api/player-identity/validate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  startSession(payload: { dynasty_id: string; role_id: string; event_id: string; identity_id?: string; custom_identity_text?: string }) {
    return request<SessionSnapshot>('/api/session/start', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  generateScript(payload: { dynasty_id: 'song' | 'late_tang' | 'ming' | 'tang'; keywords: string[] }) {
    return request<ScriptJob>('/api/scripts/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  getScriptJob(jobId: string) {
    return request<ScriptJob>(`/api/scripts/jobs/${jobId}`);
  },
  listGeneratedDemos() {
    return request<{ demos: GeneratedScriptDemo[] }>('/api/scripts/demos');
  },
  getScript(scriptId: string) {
    return request<ScriptPackage>(`/api/scripts/${scriptId}`);
  },
  validateScript(scriptId: string) {
    return request<{ passed: boolean; issues: Array<Record<string, unknown>> }>(`/api/scripts/${scriptId}/validate`, {
      method: 'POST',
    });
  },
  validateGeneratedIdentity(scriptId: string, payload: { identity_id?: string; custom_identity_text: string }) {
    return request<PlayerIdentityValidationResult>(`/api/scripts/${scriptId}/identity/validate`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  startGeneratedSession(payload: { script_id: string; identity_id?: string; custom_identity_text?: string }) {
    return request<SessionSnapshot>('/api/session/start-generated', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  getSession(sessionId: string) {
    return request<SessionSnapshot>(`/api/session/${sessionId}`);
  },
  investigate(payload: { session_id: string; scene_id: string; hotspot_id?: string; clue_id?: string | null }) {
    return request<InvestigateActionResult>('/api/investigate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  dialogue(payload: { session_id: string; npc_id: string; message: string; action_type: string; message_source: DialogueMessageSource; presented_clue_ids: string[] }) {
    return request<DialogueActionResult>('/api/dialogue', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  submitDeduction(payload: { session_id: string; deduction_id: string; selected_clue_ids: string[] }) {
    return request<DeductionSubmitResult>('/api/deduction/submit', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  choose(payload: { session_id: string; choice_id: string }) {
    return request<{ state: SessionSnapshot['state']; next: string }>('/api/choice', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  resolveEnding(payload: { session_id: string }) {
    return request<EndingResult>('/api/ending/resolve', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  getVisualStatus() {
    return request<{ api_key_available: boolean; assets: Array<{ asset_id: string; status: string; url: string }> }>('/api/visual/status');
  },
  generateCharacterPortrait(assetId: string) {
    return request<{ asset_id: string; status: string; url: string; cached?: boolean }>('/api/visual/generate', {
      method: 'POST',
      body: JSON.stringify({ asset_id: assetId }),
    });
  },
  askAssistant(payload: { session_id: string; question: string }) {
    return request<{ answer: string; suggested_focus: string[]; safety_note: string; ai_mode: string; log?: Record<string, unknown> }>('/api/assistant/hint', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};

export type { ChoiceCard };

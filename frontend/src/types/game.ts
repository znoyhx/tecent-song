export type HealthResponse = {
  status: string;
  display_text: string;
  version: string;
  mock_ai: boolean;
};

export type ApiError = {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
};

export type VisualFields = {
  visual_asset_id?: string | null;
  visual_asset_url?: string | null;
  visual_status?: 'generated' | 'fallback' | 'pending' | 'failed' | string;
};

export type Dynasty = {
  dynasty_id: string;
  name: string;
  enabled: boolean;
  period_label: string;
  core_mood: string;
  allowed_roles: string[];
  forbidden_terms: string[];
  visual_keywords: string[];
};

export type PlayerRole = {
  role_id: string;
  dynasty_id: string;
  name: string;
  enabled: boolean;
  social_position: string;
  permissions: string[];
  limitations: string[];
};

export type PlayerIdentityOption = {
  identity_id: string;
  display_name: string;
  description: string;
  social_rank: 'low' | 'middle' | 'high';
  relation_to_case: string;
  attitude_hint: string;
  background: string;
  tags: string[];
  is_default: boolean;
};

export type PlayerIdentityRecommendations = {
  default_identity: string;
  options: PlayerIdentityOption[];
};

export type PlayerIdentity = {
  identity_id: string;
  source: 'default' | 'recommended' | 'custom';
  display_name: string;
  normalized_name: string;
  description: string;
  background: string;
  social_rank: 'low' | 'middle' | 'high';
  era_fit_score: number;
  story_fit_score: number;
  tags: string[];
  is_valid: boolean;
  rejection_reason: string;
};

export type PlayerIdentityValidationResult = {
  is_valid: boolean;
  identity: PlayerIdentity | null;
  rejection_reason: string;
  suggestions: string[];
  warnings: string[];
};

export type SceneHighlight = {
  text: string;
  hotspot_id: string;
  clue_id?: string | null;
};

export type SceneHotspot = {
  hotspot_id: string;
  label: string;
  clue_ids: string[];
  description?: string;
  required_stage?: string | null;
  required_clue_ids?: string[];
  repeat_text?: string;
};

export type Scene = VisualFields & {
  scene_id: string;
  name: string;
  description: string;
  background_asset: string;
  available_stage: string[];
  npc_ids: string[];
  scene_text: string;
  highlights: SceneHighlight[];
  hotspots: SceneHotspot[];
};

export type NPCProfile = VisualFields & {
  npc_id: string;
  id?: string;
  name: string;
  dynasty?: string;
  role?: string;
  gender?: string;
  temperament?: string;
  portraitUrl?: string;
  portraitPrompt?: string;
  fallbackPortraitUrl?: string;
  avatarUrl?: string;
  imageUrl?: string;
  public_identity: string;
  public_goal: string;
  hidden_motive: string;
  known_info: string[];
  unknown_info: string[];
  forbidden_disclosure: string[];
  speaking_style: string;
  initial_trust: number;
  emotion_state: string;
  releasable_clue_ids: string[];
  stage_limits: Record<string, string>;
};


export type Clue = VisualFields & {
  clue_id: string;
  title: string;
  type: string;
  is_key: boolean;
  source_scene_id?: string | null;
  source_npc_id?: string | null;
  highlight_text: string;
  display_text: string;
  detail: string;
  stage_available: string[];
  unlock_conditions: Record<string, unknown>;
  effects: Record<string, unknown>;
  related_clue_ids: string[];
  red_highlight: boolean;
  ending_tags: string[];
  discovered: boolean;
};

export type DialogueHighlight = {
  clue_id: string;
  highlight_text: string;
  display_text: string;
};

export type ComboSummary = {
  combo_id: string;
  required_clue_ids: string[];
  result_title: string;
  result_text: string;
  effects: Record<string, unknown>;
};

export type DeductionSummary = {
  deduction_id: string;
  question: string;
  required_clue_ids: string[];
  correct_clue_ids: string[];
  wrong_feedback: string;
  success_text: string;
  effects: Record<string, unknown>;
};

export type DeductionPrompt = {
  deduction_id: string;
  question: string;
};

export type DialogueTurn = {
  turn_id: string;
  session_id: string;
  npc_id: string;
  npc_name: string;
  player_message: string;
  action_type: string;
  presented_clue_ids: string[];
  npc_response: string;
  npc_action: string;
  emotion: string;
  intent?: string;
  released_clue_ids: string[];
  highlight_clues?: DialogueHighlight[];
  red_texts?: string[];
  suggested_questions: string[];
  supervisor_notes?: string[];
  created_at: string;
};

export type ChoiceCard = {
  choice_id: string;
  title: string;
  description: string;
  effects: Record<string, unknown>;
};

export type EndingResult = VisualFields & {
  ending_id: string;
  title: string;
  summary: string;
  ending_text: string;
  history_echo: string;
  history_echo_sources?: string[];
  history_echo_ai_used?: boolean;
  history_echo_fallback_used?: boolean;
  related_clue_ids?: string[];
  related_choice_ids?: string[];
  npc_fates: Record<string, string>;
};


export type GameState = {
  session_id: string;
  event_id: string;
  dynasty_id: string;
  player_role_id: string;
  player_identity?: PlayerIdentity | null;
  current_stage: string;
  current_scene_id: string;
  discovered_clue_ids: string[];
  completed_combo_ids: string[];
  completed_deduction_ids: string[];
  npc_trust: Record<string, number>;
  flags: string[];
  scores: {
    truth: number;
    order: number;
    survival: number;
    sacrifice: number;
  };
  risk_level: number;
  available_scene_ids: string[];
  available_choice_ids: string[];
  turn_count: number;
  status: string;
  final_choice_id?: string | null;
};

export type DebugLog = {
  call_id: string;
  module: string;
  summary: string;
  success: boolean;
  fallback_used: boolean;
  supervisor_pass: boolean;
  created_at: string;
};

export type SessionSnapshot = {
  session_id: string;
  state: GameState;
  dynasty: Dynasty;
  player_role: PlayerRole;
  player_identity: PlayerIdentity | null;
  stage_label: string;
  scene: Scene;
  scene_npcs: NPCProfile[];
  available_scenes: Scene[];
  available_actions: string[];
  clues: Clue[];
  combo_summaries: ComboSummary[];
  deduction_summaries: DeductionSummary[];
  available_deductions: DeductionPrompt[];
  dialogue_turns: DialogueTurn[];
  current_goal: string;
  available_choices: ChoiceCard[];
  ending: EndingResult | null;
  ending_catalog: Array<{ ending_id: string; title: string }>;
  debug_info: {
    use_mock_ai: boolean;
    ai_provider: string;
    logs: DebugLog[];
    last_supervisor?: {
      pass: boolean;
      issues: Array<{ type: string; severity: string; detail: string }>;
      repair_instruction?: string | null;
    } | null;
  };
};

export type DialogueActionResult = {
  dialogue: {
    npc_id: string;
    npc_name: string;
    npc_dialogue: string;
    npc_action: string;
    emotion: string;
    intent?: string;
    released_clue_ids?: string[];
    highlight_clues?: DialogueHighlight[];
    red_texts?: string[];
    suggested_questions: string[];
    trust_delta?: number;
    score_delta?: Record<string, number>;
    risk_delta?: number;
    add_flags?: string[];
    supervisor_notes?: string[];
  };
  new_clues: Clue[];
  new_combos: ComboSummary[];
  new_deductions: DeductionSummary[];
  state: GameState;
  supervisor: {
    pass: boolean;
    issues: Array<{ type: string; severity: string; detail: string }>;
    repair_instruction?: string | null;
  };
  fallback_used: boolean;
  current_goal: string;
};

export type InvestigateActionResult = {
  text: string;
  new_clues: Clue[];
  new_combos: ComboSummary[];
  new_deductions: DeductionSummary[];
  state: GameState;
  scene: Scene;
  current_goal: string;
};

export type DeductionSubmitResult = {
  correct: boolean;
  feedback: string;
  deduction: DeductionSummary | DeductionPrompt;
  state: GameState;
  available_deductions: DeductionPrompt[];
  current_goal: string;
};

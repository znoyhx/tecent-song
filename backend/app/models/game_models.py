from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorPayload


class DynastyProfile(BaseModel):
    dynasty_id: str
    name: str
    enabled: bool = True
    period_label: str
    core_mood: str
    allowed_roles: list[str] = Field(default_factory=list)
    forbidden_terms: list[str] = Field(default_factory=list)
    visual_keywords: list[str] = Field(default_factory=list)


class PlayerRole(BaseModel):
    role_id: str
    dynasty_id: str
    name: str
    enabled: bool = True
    social_position: str
    permissions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class PlayerIdentityOption(BaseModel):
    identity_id: str
    display_name: str
    description: str
    social_rank: Literal["low", "middle", "high"]
    relation_to_case: str
    attitude_hint: str
    background: str
    tags: list[str] = Field(default_factory=list)
    is_default: bool = False


class PlayerIdentityRecommendations(BaseModel):
    default_identity: str
    options: list[PlayerIdentityOption]


class PlayerIdentity(BaseModel):
    identity_id: str
    source: Literal["default", "recommended", "custom"]
    display_name: str
    normalized_name: str
    description: str
    background: str
    social_rank: Literal["low", "middle", "high"]
    era_fit_score: float = 0.0
    story_fit_score: float = 0.0
    tags: list[str] = Field(default_factory=list)
    is_valid: bool = True
    rejection_reason: str = ""


class PlayerIdentityValidationRequest(BaseModel):
    dynasty_id: str = "ming"
    event_id: str
    custom_identity_text: str


class PlayerIdentityValidationResponse(BaseModel):
    is_valid: bool
    identity: PlayerIdentity | None = None
    rejection_reason: str = ""
    suggestions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SceneHighlight(BaseModel):
    text: str
    hotspot_id: str
    clue_id: str | None = None


class SceneHotspot(BaseModel):
    hotspot_id: str
    label: str
    clue_ids: list[str] = Field(default_factory=list)
    description: str = ""
    required_stage: str | None = None
    required_clue_ids: list[str] = Field(default_factory=list)
    repeat_text: str = ""


class Scene(BaseModel):
    scene_id: str
    name: str
    description: str
    background_asset: str
    available_stage: list[str] = Field(default_factory=list)
    npc_ids: list[str] = Field(default_factory=list)
    scene_text: str
    highlights: list[SceneHighlight] = Field(default_factory=list)
    hotspots: list[SceneHotspot] = Field(default_factory=list)


class NPCProfile(BaseModel):
    npc_id: str
    name: str
    public_identity: str
    public_goal: str
    hidden_motive: str
    known_info: list[str] = Field(default_factory=list)
    unknown_info: list[str] = Field(default_factory=list)
    forbidden_disclosure: list[str] = Field(default_factory=list)
    speaking_style: str
    initial_trust: int = 0
    emotion_state: str
    releasable_clue_ids: list[str] = Field(default_factory=list)
    stage_limits: dict[str, str] = Field(default_factory=dict)


class Clue(BaseModel):
    clue_id: str
    title: str
    type: str
    is_key: bool = False
    source_scene_id: str | None = None
    source_npc_id: str | None = None
    highlight_text: str
    display_text: str
    detail: str
    stage_available: list[str] = Field(default_factory=list)
    unlock_conditions: dict[str, Any] = Field(default_factory=dict)
    effects: dict[str, Any] = Field(default_factory=dict)
    related_clue_ids: list[str] = Field(default_factory=list)
    red_highlight: bool = False
    ending_tags: list[str] = Field(default_factory=list)
    unlock_by_intents: list[str] = Field(default_factory=list)
    forbidden_before_stage: str | None = None
    red_text: str | None = None
    after_unlock_flags: list[str] = Field(default_factory=list)


class ComboRule(BaseModel):
    combo_id: str
    required_clue_ids: list[str]
    result_title: str
    result_text: str
    effects: dict[str, Any] = Field(default_factory=dict)


class DeductionRule(BaseModel):
    deduction_id: str
    question: str
    required_clue_ids: list[str] = Field(default_factory=list)
    correct_clue_ids: list[str] = Field(default_factory=list)
    wrong_feedback: str
    success_text: str
    effects: dict[str, Any] = Field(default_factory=dict)


class ChapterSection(BaseModel):
    section_id: str
    stage: str
    title: str
    trigger_conditions: list[str] = Field(default_factory=list)
    scene_id: str
    npc_ids: list[str] = Field(default_factory=list)
    hotspot_ids: list[str] = Field(default_factory=list)
    clue_ids: list[str] = Field(default_factory=list)
    next_section_ids: list[str] = Field(default_factory=list)
    goal: str
    display_text: str


class ChoiceCard(BaseModel):
    choice_id: str
    title: str
    description: str
    effects: dict[str, Any] = Field(default_factory=dict)


class EventTemplate(BaseModel):
    event_id: str
    dynasty_id: str
    title: str
    surface_event: str
    hidden_truth: str
    stages: list[str]
    scene_ids: list[str]
    npc_ids: list[str]
    required_clue_ids: list[str]
    ending_rule_ids: list[str]
    choices: list[ChoiceCard] = Field(default_factory=list)
    combos: list[ComboRule] = Field(default_factory=list)
    deductions: list[DeductionRule] = Field(default_factory=list)
    chapter_sections: list[ChapterSection] = Field(default_factory=list)



class EndingRule(BaseModel):
    ending_id: str
    title: str
    priority: int
    conditions: dict[str, Any] = Field(default_factory=dict)
    required_flags: list[str] = Field(default_factory=list)
    blocked_flags: list[str] = Field(default_factory=list)
    result_summary: str
    ending_text: str
    history_echo: str
    related_clue_ids: list[str] = Field(default_factory=list)
    related_choice_ids: list[str] = Field(default_factory=list)
    npc_fates: dict[str, str] = Field(default_factory=dict)
    visual_asset_id: str | None = None
    visual_asset_url: str | None = None
    visual_status: str = "fallback"



class HistoryEchoRecord(BaseModel):
    ending_id: str
    text: str


class DialogueRuleTrigger(BaseModel):
    presented_clue_ids: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    min_trust: int | None = None
    required_flags: list[str] = Field(default_factory=list)


class DialogueHighlight(BaseModel):
    clue_id: str
    highlight_text: str
    display_text: str


class DialogueRuleResponse(BaseModel):
    npc_dialogue: str
    npc_action: str
    emotion: str
    intent: str = "ask_object"
    released_clue_ids: list[str] = Field(default_factory=list)
    highlight_clues: list[DialogueHighlight] = Field(default_factory=list)
    red_texts: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    trust_delta: int = 0
    score_delta: dict[str, int] = Field(default_factory=dict)
    risk_delta: int = 0
    add_flags: list[str] = Field(default_factory=list)
    supervisor_notes: list[str] = Field(default_factory=list)


class DialogueRule(BaseModel):
    dialogue_id: str
    stage: str
    priority: int = 0
    trigger: DialogueRuleTrigger = Field(default_factory=DialogueRuleTrigger)
    response: DialogueRuleResponse


class DialogueTurn(BaseModel):
    turn_id: str
    session_id: str
    npc_id: str
    npc_name: str
    player_message: str
    action_type: str
    presented_clue_ids: list[str] = Field(default_factory=list)
    npc_response: str
    npc_action: str
    emotion: str
    intent: str = "ask_object"
    released_clue_ids: list[str] = Field(default_factory=list)
    highlight_clues: list[DialogueHighlight] = Field(default_factory=list)
    red_texts: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    supervisor_notes: list[str] = Field(default_factory=list)
    created_at: str


class DebugLogEntry(BaseModel):
    call_id: str
    module: str
    summary: str
    success: bool
    fallback_used: bool
    supervisor_pass: bool
    created_at: str


class SupervisorIssue(BaseModel):
    type: str
    severity: Literal["low", "medium", "high"]
    detail: str


class SupervisorResult(BaseModel):
    pass_: bool = Field(alias="pass")
    issues: list[SupervisorIssue] = Field(default_factory=list)
    repair_instruction: str | None = None

    model_config = {"populate_by_name": True}


class GameScores(BaseModel):
    truth: int = 0
    order: int = 0
    survival: int = 0
    sacrifice: int = 0


class GameState(BaseModel):
    session_id: str
    event_id: str
    dynasty_id: str
    player_role_id: str
    player_identity: PlayerIdentity | None = None
    current_stage: str
    current_scene_id: str
    discovered_clue_ids: list[str] = Field(default_factory=list)
    completed_combo_ids: list[str] = Field(default_factory=list)
    completed_deduction_ids: list[str] = Field(default_factory=list)
    npc_trust: dict[str, int] = Field(default_factory=dict)
    flags: list[str] = Field(default_factory=list)
    scores: GameScores = Field(default_factory=GameScores)
    risk_level: int = 0
    available_scene_ids: list[str] = Field(default_factory=list)
    available_choice_ids: list[str] = Field(default_factory=list)
    turn_count: int = 0
    status: str = "active"
    final_choice_id: str | None = None


class SessionStartRequest(BaseModel):
    dynasty_id: str
    role_id: str
    event_id: str
    identity_id: str | None = None
    custom_identity_text: str | None = None


class DialogueRequest(BaseModel):
    session_id: str
    npc_id: str
    message: str
    action_type: str = "question"
    presented_clue_ids: list[str] = Field(default_factory=list)


class InvestigateRequest(BaseModel):
    session_id: str
    scene_id: str
    hotspot_id: str | None = None
    clue_id: str | None = None


class ChoiceRequest(BaseModel):
    session_id: str
    choice_id: str


class EndingResolveRequest(BaseModel):
    session_id: str


class DeductionSubmitRequest(BaseModel):
    session_id: str
    deduction_id: str
    selected_clue_ids: list[str] = Field(default_factory=list)

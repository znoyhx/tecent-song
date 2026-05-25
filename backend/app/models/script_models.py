from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


P0_DYNASTY_IDS = {"song", "late_tang"}
KEYWORDS_ENCODING_INVALID_MESSAGE = "关键词疑似编码损坏，请重新输入中文关键词后再生成。"
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_ASCII_ALNUM_RE = re.compile(r"[A-Za-z0-9]")
_C1_CONTROL_RE = re.compile(r"[\u0080-\u009f]")
_MOJIBAKE_RE = re.compile(r"(Ã|Â|â€|�|(?:[åçéèæä]\S*){2,})")
_PUNCTUATION_ONLY_RE = re.compile(r"^[\s\W_]+$", re.UNICODE)


def keyword_encoding_issue(keyword: str) -> str | None:
    text = str(keyword).strip()
    if not text:
        return "关键词不能为空"
    if all(char in {"?", "？", "�"} or char.isspace() for char in text):
        return KEYWORDS_ENCODING_INVALID_MESSAGE
    if _C1_CONTROL_RE.search(text) or _MOJIBAKE_RE.search(text):
        return KEYWORDS_ENCODING_INVALID_MESSAGE
    if _PUNCTUATION_ONLY_RE.fullmatch(text) and not _CJK_RE.search(text) and not _ASCII_ALNUM_RE.search(text):
        return KEYWORDS_ENCODING_INVALID_MESSAGE
    if not _CJK_RE.search(text) and not _ASCII_ALNUM_RE.search(text):
        return KEYWORDS_ENCODING_INVALID_MESSAGE
    return None


def clean_script_keywords(value: list[str]) -> list[str]:
    cleaned = [str(item).strip() for item in value if str(item).strip()]
    if not 1 <= len(cleaned) <= 8:
        raise ValueError("关键词必须为 1-8 个")
    invalid = [item for item in cleaned if keyword_encoding_issue(item)]
    if invalid:
        raise ValueError(KEYWORDS_ENCODING_INVALID_MESSAGE)
    return cleaned


class NormalizedPoint(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class NormalizedBBox(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    width: float = Field(gt=0, le=1)
    height: float = Field(gt=0, le=1)

    @model_validator(mode="after")
    def within_image(self) -> "NormalizedBBox":
        if self.x + self.width > 1 or self.y + self.height > 1:
            raise ValueError("热点范围必须落在图片 0-1 坐标内")
        return self


class ScriptOverview(BaseModel):
    title: str
    logline: str
    case_summary: str
    opening_location: str
    public_objective: str
    major_locations: list[str] = Field(default_factory=list)
    major_npcs: list[str] = Field(default_factory=list)
    player_briefing: str


class PlayableIdentity(BaseModel):
    identity_id: str
    display_name: str
    description: str
    social_rank: Literal["low", "middle", "high"]
    relation_to_case: str
    motive: str
    permissions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    background: str
    tags: list[str] = Field(default_factory=list)
    is_default: bool = False


class ScriptWorld(BaseModel):
    dynasty_id: Literal["song", "late_tang"]
    dynasty_name: str
    era_name: str
    year_hint: str
    location_region: str
    rules: list[str] = Field(default_factory=list)
    forbidden_terms: list[str] = Field(default_factory=list)


class ScriptStory(BaseModel):
    surface_event: str
    hidden_truth: str
    themes: list[str] = Field(default_factory=list)
    culprit_boundary: str
    truth_chain_clue_ids: list[str] = Field(default_factory=list)


class ScriptStage(BaseModel):
    stage_id: Literal["intro", "investigation", "reversal", "choice", "ending"]
    name: str
    order: int
    goal: str
    entry_location_id: str
    unlock_conditions: list[str] = Field(default_factory=list)
    available_location_ids: list[str] = Field(default_factory=list)
    key_clue_ids: list[str] = Field(default_factory=list)


class ScriptLocationHotspot(BaseModel):
    hotspot_id: str
    label: str
    description: str
    clue_ids: list[str] = Field(default_factory=list)
    required_stage: str | None = None
    required_clue_ids: list[str] = Field(default_factory=list)
    investigation_text: str
    repeat_text: str = ""
    anchor_point: NormalizedPoint | None = None
    bbox: NormalizedBBox | None = None


class ScriptLocation(BaseModel):
    location_id: str
    name: str
    description: str
    scene_text: str
    stage_ids: list[str] = Field(default_factory=list)
    npc_ids: list[str] = Field(default_factory=list)
    hotspots: list[ScriptLocationHotspot] = Field(default_factory=list)
    visual_asset_id: str


class ScriptNPC(BaseModel):
    npc_id: str
    name: str
    public_identity: str
    appearance: str
    personality: str
    background_suspicion: str
    case_connection: str
    event_behavior: str
    public_goal: str
    hidden_motive: str
    known_info: list[str] = Field(default_factory=list)
    unknown_info: list[str] = Field(default_factory=list)
    forbidden_disclosure: list[str] = Field(default_factory=list)
    speaking_style: str
    initial_trust: int = 0
    emotion_state: str = "guarded"
    releasable_clue_ids: list[str] = Field(default_factory=list)
    stage_limits: dict[str, str] = Field(default_factory=dict)
    visual_asset_id: str


class ScriptRelationship(BaseModel):
    source_id: str
    target_id: str
    relation: str
    public_state: str
    hidden_state: str = ""


class ScriptClue(BaseModel):
    clue_id: str
    title: str
    type: str
    is_key: bool = False
    source_location_id: str | None = None
    source_npc_id: str | None = None
    highlight_text: str
    display_text: str
    detail: str
    stage_available: list[str] = Field(default_factory=list)
    unlock_conditions: dict[str, Any] = Field(default_factory=dict)
    effects: dict[str, Any] = Field(default_factory=dict)
    related_clue_ids: list[str] = Field(default_factory=list)
    ending_tags: list[str] = Field(default_factory=list)
    forbidden_before_stage: str | None = None
    visual_asset_id: str


class ClueGraphRule(BaseModel):
    rule_id: str
    required_clue_ids: list[str]
    result_title: str
    result_text: str
    effects: dict[str, Any] = Field(default_factory=dict)


class ScriptDeduction(BaseModel):
    deduction_id: str
    question: str
    required_clue_ids: list[str] = Field(default_factory=list)
    correct_clue_ids: list[str] = Field(default_factory=list)
    wrong_feedback: str
    success_text: str
    effects: dict[str, Any] = Field(default_factory=dict)


class ScriptChapterSection(BaseModel):
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


class ScriptDialogueRule(BaseModel):
    dialogue_id: str
    npc_id: str
    stage: str
    priority: int = 0
    trigger_keywords: list[str] = Field(default_factory=list)
    presented_clue_ids: list[str] = Field(default_factory=list)
    response: str
    released_clue_ids: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)


class ScriptChoice(BaseModel):
    choice_id: str
    title: str
    description: str
    effects: dict[str, Any] = Field(default_factory=dict)


class ScriptEnding(BaseModel):
    ending_id: str
    title: str
    priority: int = 0
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


class ImageQualityGateResult(BaseModel):
    status: Literal["pending", "generated", "approved", "rejected", "blocked"] = "pending"
    checked_at: str | None = None
    attempts: int = 0
    prompt_hash: str | None = None
    issues: list[str] = Field(default_factory=list)
    approved_path: str | None = None
    rejected_paths: list[str] = Field(default_factory=list)
    regenerated_count: int = 0


class VisualAsset(BaseModel):
    asset_id: str
    asset_type: Literal["scene", "npc", "clue", "ending"]
    owner_id: str
    title: str
    prompt: str
    negative_prompt: str = ""
    required_subjects: list[str] = Field(default_factory=list)
    era_feature_checklist: list[str] = Field(default_factory=list)
    prompt_hash: str | None = None
    generated_path: str | None = None
    url: str | None = None
    provider: str | None = None
    model: str | None = None
    generation_status: Literal["pending", "generated", "approved", "rejected", "blocked"] = "pending"
    quality_gate: ImageQualityGateResult = Field(default_factory=ImageQualityGateResult)


class VisualStyleGuide(BaseModel):
    style_keywords: list[str]
    forbidden_visuals: list[str] = Field(default_factory=list)
    color_script: str
    camera: str
    era_feature_checklist: list[str]
    appearance_lock: dict[str, str] = Field(default_factory=dict)


class HotspotPositioning(BaseModel):
    location_id: str
    hotspot_id: str
    visual_asset_id: str
    clue_id: str | None = None
    anchor_point: NormalizedPoint
    bbox: NormalizedBBox
    calibration_status: Literal["pending", "approved", "blocked"] = "pending"
    calibrated_against_path: str | None = None


class QualityGateSummary(BaseModel):
    required_scene_count: int = 8
    required_npc_count: int = 4
    required_clue_count: int = 6
    scene_approved: int = 0
    npc_approved: int = 0
    clue_approved: int = 0
    rejected: int = 0
    regenerated: int = 0
    blocked: int = 0


class ScriptPackage(BaseModel):
    script_id: str
    job_id: str | None = None
    dynasty_id: Literal["song", "late_tang"]
    keywords: list[str] = Field(min_length=1, max_length=8)
    generation_source: Literal["deepseek"] = "deepseek"
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    script_overview: ScriptOverview
    playable_identities: list[PlayableIdentity] = Field(min_length=1)
    world: ScriptWorld
    story: ScriptStory
    stages: list[ScriptStage] = Field(min_length=1)
    locations: list[ScriptLocation] = Field(min_length=1)
    npcs: list[ScriptNPC] = Field(min_length=1)
    relationships: list[ScriptRelationship] = Field(default_factory=list)
    clues: list[ScriptClue] = Field(min_length=1)
    clue_graph: list[ClueGraphRule] = Field(default_factory=list)
    deductions: list[ScriptDeduction] = Field(default_factory=list)
    chapter_sections: list[ScriptChapterSection] = Field(default_factory=list)
    dialogue_rules: list[ScriptDialogueRule] = Field(default_factory=list)
    choices: list[ScriptChoice] = Field(default_factory=list)
    endings: list[ScriptEnding] = Field(min_length=1)
    visual_assets: list[VisualAsset] = Field(default_factory=list)
    visual_style_guide: VisualStyleGuide
    hotspot_positioning: list[HotspotPositioning] = Field(default_factory=list)
    quality_gate: QualityGateSummary = Field(default_factory=QualityGateSummary)

    @field_validator("keywords")
    @classmethod
    def clean_keywords(cls, value: list[str]) -> list[str]:
        return clean_script_keywords(value)

    @model_validator(mode="after")
    def ensure_world_matches(self) -> "ScriptPackage":
        if self.world.dynasty_id != self.dynasty_id:
            raise ValueError("world.dynasty_id 必须与剧本 dynasty_id 一致")
        return self


class ScriptGenerateRequest(BaseModel):
    dynasty_id: Literal["song", "late_tang"]
    keywords: list[str] = Field(min_length=1, max_length=8)

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, value: list[str]) -> list[str]:
        return clean_script_keywords(value)


class ScriptJobStep(BaseModel):
    step_id: str
    title: str
    description: str
    status: Literal["pending", "running", "passed", "failed", "blocked", "retrying"] = "pending"
    message: str = ""
    attempts: int = 0
    started_at: str | None = None
    completed_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TransitionalQuote(BaseModel):
    text: str
    author: str
    source: str = ""


class VisualQualitySummary(BaseModel):
    scene: dict[str, int] = Field(default_factory=lambda: {"required": 8, "approved": 0, "rejected": 0, "regenerated": 0, "blocked": 0})
    npc: dict[str, int] = Field(default_factory=lambda: {"required": 4, "approved": 0, "rejected": 0, "regenerated": 0, "blocked": 0})
    clue: dict[str, int] = Field(default_factory=lambda: {"required": 6, "approved": 0, "rejected": 0, "regenerated": 0, "blocked": 0})


class ScriptJob(BaseModel):
    job_id: str
    dynasty_id: Literal["song", "late_tang"]
    keywords: list[str]
    status: Literal["queued", "running", "completed", "failed", "visual_blocked"] = "queued"
    progress: int = 0
    current_step: str = "queued"
    steps: list[ScriptJobStep]
    blocking_issues: list[dict[str, Any]] = Field(default_factory=list)
    transitional_quote: TransitionalQuote | None = None
    visual_quality: VisualQualitySummary = Field(default_factory=VisualQualitySummary)
    ready_for_overview: bool = False
    script_id: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    ai_calls: list[dict[str, Any]] = Field(default_factory=list)


class StartGeneratedRequest(BaseModel):
    script_id: str
    identity_id: str | None = None
    custom_identity_text: str | None = None

    @model_validator(mode="after")
    def require_identity(self) -> "StartGeneratedRequest":
        if not (self.identity_id or (self.custom_identity_text and self.custom_identity_text.strip())):
            raise ValueError("必须选择身份或填写自定义身份")
        return self

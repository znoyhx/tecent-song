from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from app.models.game_models import Clue, DialogueHighlight, DialogueRuleResponse, DialogueTurn, GameState, NPCProfile, PlayerIdentity


SUPPORTED_INTENTS = {
    "ask_timeline",
    "ask_location",
    "ask_object",
    "ask_relationship",
    "ask_motive",
    "accuse",
    "smalltalk",
    "off_topic",
    "force_truth",
}


@dataclass
class ScriptBoundChatContext:
    player_message: str
    intent: str
    npc_id: str
    current_stage: str
    npc_trust: int
    discovered_clue_ids: list[str]
    candidate_clue_ids: list[str] = field(default_factory=list)
    preferred_clue_ids: list[str] = field(default_factory=list)
    allowed_released_clue_ids: list[str] = field(default_factory=list)
    blocked_clues: list[dict[str, str]] = field(default_factory=list)
    recent_turns: list[dict[str, Any]] = field(default_factory=list)
    suggested_questions: list[str] = field(default_factory=list)
    red_texts: list[str] = field(default_factory=list)
    supervisor_notes: list[str] = field(default_factory=list)
    player_identity_display: str = ""
    player_identity_rank: str = "middle"


class ScriptBoundChatService:
    """Rule-first clue probing for free-form NPC questions."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.intent_rules = self._read_json("dialogue_intents.json").get("intents", [])
        self.chat_policies = self._read_json("npc_chat_policies.json").get("policies", {})
        self.default_policy = self._read_json("npc_chat_policies.json").get("default_policy", {})

    def prepare_context(
        self,
        *,
        state: GameState,
        npc: NPCProfile,
        player_message: str,
        clue_map: dict[str, Clue],
        dialogue_turns: list[DialogueTurn],
        presented_clue_ids: list[str] | None = None,
        player_identity: PlayerIdentity | None = None,
    ) -> ScriptBoundChatContext:
        intent = self.classify_intent(player_message)
        if intent == "off_topic" and presented_clue_ids:
            intent = "ask_object"
        npc_trust = state.npc_trust.get(npc.npc_id, npc.initial_trust)
        allowed, blocked = self._legal_npc_clues(state=state, npc=npc, clue_map=clue_map)
        candidates = self._candidate_clues(
            intent=intent,
            npc=npc,
            message=player_message,
            clue_map=clue_map,
            presented_clue_ids=presented_clue_ids or [],
        )
        preferred = [clue_id for clue_id in candidates if clue_id in allowed]
        suggested = self._suggested_questions(
            intent=intent,
            npc=npc,
            state=state,
            clue_map=clue_map,
            preferred_clue_ids=preferred,
            allowed_clue_ids=allowed,
        )
        notes = [
            f"识别意图：{intent}",
            f"当前阶段：{state.current_stage}",
            f"当前 NPC 可合法释放线索：{len(allowed)} 条",
        ]
        if blocked:
            notes.append("存在被阶段、前置线索或信任度拦截的线索。")
        return ScriptBoundChatContext(
            player_message=player_message,
            intent=intent,
            npc_id=npc.npc_id,
            current_stage=state.current_stage,
            npc_trust=npc_trust,
            discovered_clue_ids=list(state.discovered_clue_ids),
            candidate_clue_ids=candidates,
            preferred_clue_ids=preferred,
            allowed_released_clue_ids=allowed,
            blocked_clues=blocked,
            recent_turns=[turn.model_dump() for turn in dialogue_turns if turn.npc_id == npc.npc_id][-4:],
            suggested_questions=suggested,
            supervisor_notes=notes,
            player_identity_display=player_identity.display_name if player_identity else "",
            player_identity_rank=player_identity.social_rank if player_identity else "middle",
        )

    def classify_intent(self, player_message: str) -> str:
        message = player_message.strip()
        if not message:
            return "smalltalk"
        for rule in self.intent_rules:
            intent = str(rule.get("intent", "")).strip()
            keywords = [str(item) for item in rule.get("keywords", [])]
            if intent in SUPPORTED_INTENTS and any(keyword and keyword in message for keyword in keywords):
                return intent
        return "off_topic"

    def response_for_context(
        self,
        *,
        base_response: DialogueRuleResponse,
        context: ScriptBoundChatContext,
        npc: NPCProfile,
        clue_map: dict[str, Clue],
        rule_matched: bool,
    ) -> DialogueRuleResponse:
        if context.intent in {"smalltalk", "off_topic"}:
            return self._smalltalk_response(context=context, npc=npc, clue_map=clue_map)
        if context.intent == "force_truth":
            return self._force_truth_response(context=context, npc=npc)

        response = base_response.model_copy(deep=True)
        response.intent = context.intent
        response.supervisor_notes = list(context.supervisor_notes)

        if not rule_matched and not response.released_clue_ids and context.preferred_clue_ids:
            return self._clue_probe_response(context=context, npc=npc, clue_map=clue_map)

        response.released_clue_ids = self.filter_released_clue_ids(response.released_clue_ids, context)
        return self.finalize_response(response=response, context=context, clue_map=clue_map)

    def finalize_response(
        self,
        *,
        response: DialogueRuleResponse,
        context: ScriptBoundChatContext,
        clue_map: dict[str, Clue],
    ) -> DialogueRuleResponse:
        response.intent = context.intent
        response.released_clue_ids = self.filter_released_clue_ids(response.released_clue_ids, context)
        response.highlight_clues = self._highlights_for_response(response=response, clue_map=clue_map)
        response.red_texts = self._red_texts_for_response(response=response)
        response.suggested_questions = self._three_questions(response.suggested_questions or context.suggested_questions)
        if not response.supervisor_notes:
            response.supervisor_notes = list(context.supervisor_notes)
        return response

    def filter_released_clue_ids(self, released_clue_ids: list[str], context: ScriptBoundChatContext) -> list[str]:
        allowed = set(context.allowed_released_clue_ids)
        filtered: list[str] = []
        for clue_id in released_clue_ids:
            if clue_id in allowed and clue_id not in filtered:
                filtered.append(clue_id)
        return filtered

    def _read_json(self, relative_path: str) -> dict[str, Any]:
        path = self.data_dir / relative_path
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _policy_for(self, npc_id: str) -> dict[str, Any]:
        policy = dict(self.default_policy)
        policy.update(self.chat_policies.get(npc_id, {}))
        return policy

    def _legal_npc_clues(
        self,
        *,
        state: GameState,
        npc: NPCProfile,
        clue_map: dict[str, Clue],
    ) -> tuple[list[str], list[dict[str, str]]]:
        allowed: list[str] = []
        blocked: list[dict[str, str]] = []
        for clue_id in npc.releasable_clue_ids:
            clue = clue_map.get(clue_id)
            if clue is None:
                blocked.append({"clue_id": clue_id, "reason": "线索不存在"})
                continue
            reason = self._release_block_reason(state=state, clue=clue)
            if reason:
                blocked.append({"clue_id": clue_id, "reason": reason})
                continue
            allowed.append(clue_id)
        return allowed, blocked

    def _release_block_reason(self, *, state: GameState, clue: Clue) -> str:
        if state.current_stage not in clue.stage_available:
            return "当前剧情阶段不允许释放"
        if clue.forbidden_before_stage:
            stage_order = {"intro": 0, "investigation": 1, "reversal": 2, "choice": 3, "ending": 4}
            if stage_order.get(state.current_stage, 0) < stage_order.get(clue.forbidden_before_stage, 0):
                return "尚未到达允许披露阶段"

        conditions = clue.unlock_conditions or {}
        discovered = set(state.discovered_clue_ids)
        flags = set(state.flags)

        required_clue_ids = set(conditions.get("required_clue_ids", []))
        if not required_clue_ids.issubset(discovered):
            return "缺少前置线索"

        required_flags = set(conditions.get("required_flags", []))
        if not required_flags.issubset(flags):
            return "缺少前置状态"

        min_risk = conditions.get("min_risk")
        if min_risk is not None and state.risk_level < int(min_risk):
            return "风险值不足"

        max_risk = conditions.get("max_risk")
        if max_risk is not None and state.risk_level > int(max_risk):
            return "风险值过高"

        min_trust = conditions.get("min_trust")
        if isinstance(min_trust, dict):
            for npc_id, required_value in min_trust.items():
                if state.npc_trust.get(npc_id, 0) < int(required_value):
                    return "信任度不足"
        elif min_trust is not None and clue.source_npc_id:
            if state.npc_trust.get(clue.source_npc_id, 0) < int(min_trust):
                return "信任度不足"

        return ""

    def _candidate_clues(
        self,
        *,
        intent: str,
        npc: NPCProfile,
        message: str,
        clue_map: dict[str, Clue],
        presented_clue_ids: list[str],
    ) -> list[str]:
        policy = self._policy_for(npc.npc_id)
        mapped = list(policy.get("intent_clue_map", {}).get(intent, []))
        related_to_presented: list[str] = []
        for presented_id in presented_clue_ids:
            presented_clue = clue_map.get(presented_id)
            if presented_clue is None:
                continue
            related_to_presented.extend(presented_clue.related_clue_ids)
        message_hits: list[str] = []
        for clue_id in npc.releasable_clue_ids:
            clue = clue_map.get(clue_id)
            if clue is None:
                continue
            haystack = f"{clue.title}{clue.highlight_text}{clue.display_text}{clue.detail}"
            if any(token and token in haystack for token in self._message_tokens(message)):
                message_hits.append(clue_id)

        combined = [*related_to_presented, *message_hits, *mapped, *npc.releasable_clue_ids]
        unique: list[str] = []
        for clue_id in combined:
            if clue_id in npc.releasable_clue_ids and clue_id not in unique:
                unique.append(clue_id)
        return unique

    def _message_tokens(self, message: str) -> list[str]:
        fixed_terms = [
            "旧书箱",
            "书箱",
            "箱",
            "焦痕",
            "灯油",
            "残页",
            "火油",
            "后门",
            "门闩",
            "袖口",
            "旧墨",
            "红印",
            "账册",
            "稿",
            "封口令",
            "封口",
            "链路",
            "搜检",
            "城门",
            "纸线",
            "外皮",
        ]
        return [term for term in fixed_terms if term in message]

    def _smalltalk_response(
        self,
        *,
        context: ScriptBoundChatContext,
        npc: NPCProfile,
        clue_map: dict[str, Clue],
    ) -> DialogueRuleResponse:
        policy = self._policy_for(npc.npc_id)
        anchors = policy.get("mainline_anchors", ["旧书箱", "后门泥痕", "残页"])
        hook = "、".join(str(item) for item in anchors[:3])
        line = str(policy.get("smalltalk_reply") or f"{npc.name}短短应了一句，随即把话收回案情。眼下更要紧的是{hook}。")
        return self.finalize_response(
            response=DialogueRuleResponse(
                npc_dialogue=line,
                npc_action=str(policy.get("smalltalk_action") or "对方没有顺着闲话展开，只把目光转回案发处。"),
                emotion=self._safe_emotion(npc.emotion_state),
                intent=context.intent,
                released_clue_ids=[],
                suggested_questions=context.suggested_questions,
                trust_delta=0,
                score_delta={},
                risk_delta=0,
                add_flags=[],
                supervisor_notes=[*context.supervisor_notes, "闲聊已限制为短回应并回钩主线。"],
            ),
            context=context,
            clue_map=clue_map,
        )

    def _force_truth_response(self, *, context: ScriptBoundChatContext, npc: NPCProfile) -> DialogueRuleResponse:
        policy = self._policy_for(npc.npc_id)
        line = str(
            policy.get("force_truth_reply")
            or f"{npc.name}脸色一沉：这话不能这样问。我只说我亲眼见过的，其余不能替你定案。"
        )
        return DialogueRuleResponse(
            npc_dialogue=line,
            npc_action=str(policy.get("force_truth_action") or "对方压低声音，避开了足以定案的说法。"),
            emotion="defensive",
            intent="force_truth",
            released_clue_ids=[],
            highlight_clues=[],
            red_texts=[],
            suggested_questions=self._three_questions(context.suggested_questions),
            trust_delta=0,
            score_delta={},
            risk_delta=0,
            add_flags=[],
            supervisor_notes=[*context.supervisor_notes, "强行套真相未释放最终事实。"],
        )

    def _clue_probe_response(
        self,
        *,
        context: ScriptBoundChatContext,
        npc: NPCProfile,
        clue_map: dict[str, Clue],
    ) -> DialogueRuleResponse:
        clue = clue_map[context.preferred_clue_ids[0]]
        line = (
            f"{npc.name}斟酌片刻，终于顺着你的追问开口：{clue.display_text}"
            f" 这话只能先说到这里。"
        )
        return self.finalize_response(
            response=DialogueRuleResponse(
                npc_dialogue=line,
                npc_action=f"{npc.name}避开旁人的视线，声音压得更低。",
                emotion=self._safe_emotion(npc.emotion_state),
                intent=context.intent,
                released_clue_ids=[clue.clue_id],
                suggested_questions=context.suggested_questions,
                trust_delta=1 if context.npc_trust < 2 else 0,
                score_delta={},
                risk_delta=0,
                add_flags=[],
                supervisor_notes=context.supervisor_notes,
            ),
            context=context,
            clue_map=clue_map,
        )

    def _suggested_questions(
        self,
        *,
        intent: str,
        npc: NPCProfile,
        state: GameState,
        clue_map: dict[str, Clue],
        preferred_clue_ids: list[str],
        allowed_clue_ids: list[str],
    ) -> list[str]:
        policy = self._policy_for(npc.npc_id)
        questions = list(policy.get("suggested_by_intent", {}).get(intent, []))
        for clue_id in [*preferred_clue_ids, *allowed_clue_ids]:
            clue = clue_map.get(clue_id)
            if clue is None:
                continue
            questions.append(f"关于{clue.highlight_text}，你还隐瞒了什么？")
            questions.append(f"{clue.title}和昨夜的火有什么关系？")
        if state.current_stage in {"reversal", "choice"}:
            questions.append("这条线索能不能和封口令对上？")
        return self._three_questions(questions)

    def _three_questions(self, questions: list[str]) -> list[str]:
        fallback = [
            "昨夜旧书箱是谁动过？",
            "后门泥痕能说明什么？",
            "残页为什么不能离开书坊？",
        ]
        cleaned: list[str] = []
        for question in [*questions, *fallback]:
            item = str(question).strip()
            if not item:
                continue
            if not item.endswith("？"):
                item = f"{item.rstrip('?.!！。')}？"
            if item not in cleaned:
                cleaned.append(item)
            if len(cleaned) == 3:
                break
        return cleaned

    def _highlights_for_response(
        self,
        *,
        response: DialogueRuleResponse,
        clue_map: dict[str, Clue],
    ) -> list[DialogueHighlight]:
        highlights: list[DialogueHighlight] = []
        full_text = response.npc_dialogue
        for clue_id in response.released_clue_ids:
            clue = clue_map.get(clue_id)
            if clue is None:
                continue
            highlight_text = self._matching_highlight_text(clue=clue, full_text=full_text)
            if highlight_text:
                highlights.append(
                    DialogueHighlight(
                        clue_id=clue.clue_id,
                        highlight_text=highlight_text,
                        display_text=clue.display_text,
                    )
                )
        return highlights

    def _matching_highlight_text(self, *, clue: Clue, full_text: str) -> str:
        candidates = [clue.red_text or "", clue.highlight_text, clue.title]
        for candidate in candidates:
            if candidate and candidate in full_text:
                return candidate
        for candidate in candidates:
            for token in self._highlight_tokens(candidate):
                if token in full_text:
                    return token
        return ""

    def _highlight_tokens(self, text: str) -> list[str]:
        separators = ["，", "。", "、", "的", "没", "不", "和", "与"]
        tokens = [text]
        for separator in separators:
            next_tokens: list[str] = []
            for token in tokens:
                next_tokens.extend(part for part in token.split(separator) if part)
            tokens = next_tokens
        return [token for token in tokens if len(token) >= 2]

    def _red_texts_for_response(self, *, response: DialogueRuleResponse) -> list[str]:
        texts = [item.highlight_text for item in response.highlight_clues if item.highlight_text]
        for text in response.red_texts:
            if text and text not in texts:
                texts.append(text)
        return texts

    def _safe_emotion(self, emotion: str) -> str:
        if emotion in {"fearful", "calm", "angry", "hesitant", "defensive"}:
            return emotion
        if emotion in {"anxious", "guarded", "uneasy", "pleading", "stern"}:
            return "hesitant"
        if emotion == "resolute":
            return "calm"
        return "hesitant"

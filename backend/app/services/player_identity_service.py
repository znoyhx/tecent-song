from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings, settings
from app.models.game_models import (
    DynastyProfile,
    EventTemplate,
    PlayerIdentity,
    PlayerIdentityOption,
    PlayerIdentityRecommendations,
    PlayerIdentityValidationResponse,
)
from app.services.ai_client import AIClient


IDENTITY_SCHEMA_HINT: dict[str, Any] = {
    "is_valid": True,
    "normalized_name": "中文身份名",
    "display_name": "中文身份名",
    "social_rank": "low|middle|high",
    "era_fit_score": 0.8,
    "story_fit_score": 0.8,
    "background_seed": "中文背景种子",
    "warnings": [],
    "rejection_reason": "",
    "suggestions": [],
}


@dataclass
class IdentityValidationError(Exception):
    message: str
    suggestions: list[str]


class PlayerIdentityService:
    def __init__(self, *, ai_client: AIClient | None = None, runtime_settings: Settings | None = None) -> None:
        self.settings = runtime_settings or settings
        self.ai_client = ai_client or AIClient(self.settings)
        self.modern_political_terms = {
            "国民党",
            "共产党",
            "美国总统",
            "总统",
            "国家主席",
            "现代部长",
            "部长",
            "议员",
            "国会",
            "现代军官",
            "军官",
            "政党",
            "委员",
        }
        self.modern_job_terms = {
            "程序员",
            "黑客",
            "飞行员",
            "特工",
            "记者",
            "主播",
            "网红",
            "警察",
            "律师",
            "工程师",
            "科学家",
            "现代医生",
        }
        self.historical_person_terms = {"朱元璋", "秦始皇", "李白", "朱棣", "刘伯温", "张居正", "海瑞", "诸葛亮"}
        self.world_breaking_terms = {
            "神仙",
            "仙人",
            "妖怪",
            "外星人",
            "穿越者",
            "机器人",
            "皇帝",
            "天子",
            "太子",
            "皇后",
            "火枪",
            "枪",
            "大炮",
            "坦克",
            "手机",
            "电脑",
            "互联网",
            "电报",
            "电话",
            "汽车",
        }
        self.injection_terms = {
            "忽略",
            "系统提示",
            "提示词",
            "开发者",
            "prompt",
            "jailbreak",
            "api",
            "key",
            "密钥",
            "删除规则",
            "输出规则",
            "扮演系统",
            "色情",
            "傻逼",
        }

    def recommendations_for(self, *, dynasty: DynastyProfile, event: EventTemplate) -> PlayerIdentityRecommendations:
        if dynasty.dynasty_id == "ming" and event.event_id == "ming_bookshop_fire":
            options = [
                PlayerIdentityOption(
                    identity_id="bookshop_apprentice",
                    display_name="书坊学徒",
                    description="熟悉书坊日常，也最容易被卷入嫌疑。",
                    social_rank="low",
                    relation_to_case="你本就在书坊守夜，能接触纸稿、账册和后院火场。",
                    attitude_hint="多数 NPC 会把你当作可驱使的小人物，轻慢中带着试探。",
                    background="你是书坊里打杂守夜的学徒，熟悉纸张、刻版和前后院动线。雨夜火起后，掌柜与差役都把目光投向你，你必须先在疑影中自证清白。",
                    tags=["书坊", "守夜", "低身份", "可调查"],
                    is_default=True,
                ),
                PlayerIdentityOption(
                    identity_id="wandering_detective",
                    display_name="游方探事人",
                    description="擅长查访人情，但身份容易惹人防备。",
                    social_rank="middle",
                    relation_to_case="你为一桩旧稿纠纷来到书坊附近，恰逢雨夜失火。",
                    attitude_hint="NPC 会半信半疑，愿听你追问，却会防着你把事情闹大。",
                    background="你以替商旅查访失物和旧案为生，随身带着磨旧的问事札。雨夜途经书坊，本想打听一卷旧稿去向，却被火光和封门差役留在现场。",
                    tags=["探事", "查访", "中身份", "易盘问"],
                ),
                PlayerIdentityOption(
                    identity_id="lodging_scholar",
                    display_name="寄居书生",
                    description="识字懂文书，容易接近士人与稿件。",
                    social_rank="middle",
                    relation_to_case="你在城中借读，曾与书坊往来抄校文稿。",
                    attitude_hint="士人愿与你多说几句，官面人物仍会怀疑你的立场。",
                    background="你是寄居城中的书生，靠抄校文稿换些盘缠。因曾替书坊核过纸样，雨夜被叫来辨认残稿，却在封门声中发现自己也脱不开干系。",
                    tags=["读书人", "文书", "中身份", "可接近士子"],
                ),
                PlayerIdentityOption(
                    identity_id="woodcutter",
                    display_name="近郊樵夫",
                    description="从后巷送柴入城，行动不起眼却常被轻视。",
                    social_rank="low",
                    relation_to_case="你夜里给书坊送柴，正好经过后门与雨巷。",
                    attitude_hint="NPC 可能轻慢、敷衍或怀疑你图利，证据足够时才会动摇。",
                    background="你是近郊樵夫，入城送柴时常从书坊后巷经过。雨夜你本想把湿柴卸在檐下避雨，却撞见后院火起，粗布衣衫反让旁人先疑你偷摸。",
                    tags=["樵夫", "低身份", "后巷", "不易被注意"],
                ),
                PlayerIdentityOption(
                    identity_id="wandering_physician",
                    display_name="游方郎中",
                    description="以问诊为名能接近伤者和惊惧之人。",
                    social_rank="middle",
                    relation_to_case="你被请来查看烟呛与烫伤，因而留在书坊。",
                    attitude_hint="NPC 会试探你的来意，受惊者更可能逐步信任你。",
                    background="你是走街串巷的游方郎中，夜里被人喊来查看烟呛与烫伤。你原只想开两味安神药，却发现众人的惊惧并不只来自火势。",
                    tags=["郎中", "中身份", "安抚", "易接近伤者"],
                ),
                PlayerIdentityOption(
                    identity_id="retired_official",
                    display_name="致仕高官",
                    description="有名望与官场阅历，但一举一动都被谨慎盯着。",
                    social_rank="high",
                    relation_to_case="你因旧日藏书与书坊往来，雨夜被卷入封锁现场。",
                    attitude_hint="NPC 多会恭敬谨慎，却更可能避重就轻，害怕担责。",
                    background="你是致仕在家的旧官，因爱藏旧版书与书坊有往来。雨夜本是来取修补书函，却遇后院火起；名望让人不敢怠慢，也让每句话都被官面记在心上。",
                    tags=["高官", "名望", "高身份", "受忌惮"],
                ),
            ]
            return PlayerIdentityRecommendations(default_identity="bookshop_apprentice", options=options)

        fallback = [
            PlayerIdentityOption(
                identity_id="default_scholar",
                display_name="书生",
                description="识字懂礼，适合进入多数历史疑案。",
                social_rank="middle",
                relation_to_case="因借读、抄书或访友来到案发附近。",
                attitude_hint="NPC 会半信半疑，随证据逐步信任。",
                background="你是途经此地的书生，因借宿或抄书来到案发附近。事件突起时，你没有官面权力，只能凭眼前线索和言语试探慢慢靠近真相。",
                tags=["读书人", "中身份"],
                is_default=True,
            )
        ]
        return PlayerIdentityRecommendations(default_identity="default_scholar", options=fallback)

    def resolve_for_session(
        self,
        *,
        dynasty: DynastyProfile,
        event: EventTemplate,
        identity_id: str | None,
        custom_identity_text: str | None,
    ) -> PlayerIdentity:
        custom_text = (custom_identity_text or "").strip()
        if custom_text:
            validated = self.validate_custom(dynasty=dynasty, event=event, custom_identity_text=custom_text)
            if not validated.is_valid or validated.identity is None:
                raise IdentityValidationError(validated.rejection_reason, validated.suggestions)
            return validated.identity

        recommendations = self.recommendations_for(dynasty=dynasty, event=event)
        selected_id = identity_id or recommendations.default_identity
        for option in recommendations.options:
            if option.identity_id == selected_id:
                source = "default" if option.is_default or selected_id == recommendations.default_identity else "recommended"
                return self._identity_from_option(option, source=source)
        raise IdentityValidationError("未找到这个推荐身份，请重新选择。", self.default_suggestions())

    def validate_custom(
        self,
        *,
        dynasty: DynastyProfile,
        event: EventTemplate,
        custom_identity_text: str,
    ) -> PlayerIdentityValidationResponse:
        text = self._clean_text(custom_identity_text)
        rejection = self._rule_rejection(text, dynasty=dynasty)
        if rejection:
            return PlayerIdentityValidationResponse(
                is_valid=False,
                rejection_reason=rejection,
                suggestions=self.default_suggestions(),
            )

        if self._can_use_ai():
            ai_result = self._validate_with_ai(dynasty=dynasty, event=event, text=text)
            if ai_result is not None:
                return ai_result

        identity = self._heuristic_identity(dynasty=dynasty, event=event, text=text)
        return PlayerIdentityValidationResponse(
            is_valid=True,
            identity=identity,
            warnings=["AI 暂不可用，已使用本地规则完成身份校验。"],
        )

    def default_suggestions(self) -> list[str]:
        return ["书生", "樵夫", "游方探事人"]

    def _identity_from_option(self, option: PlayerIdentityOption, *, source: str) -> PlayerIdentity:
        return PlayerIdentity(
            identity_id=option.identity_id,
            source=source,  # type: ignore[arg-type]
            display_name=option.display_name,
            normalized_name=option.display_name,
            description=option.description,
            background=option.background,
            social_rank=option.social_rank,
            era_fit_score=0.96,
            story_fit_score=0.9,
            tags=option.tags,
            is_valid=True,
            rejection_reason="",
        )

    def _heuristic_identity(self, *, dynasty: DynastyProfile, event: EventTemplate, text: str) -> PlayerIdentity:
        social_rank = self._rank_for(text)
        normalized_name = self._normalized_name(text, social_rank)
        description = self._description_for(display_name=text, social_rank=social_rank)
        background = self._background_for(display_name=text, normalized_name=normalized_name, social_rank=social_rank, event=event)
        return PlayerIdentity(
            identity_id=f"custom_{abs(hash(text)) % 10_000_000}",
            source="custom",
            display_name=text,
            normalized_name=normalized_name,
            description=description,
            background=background,
            social_rank=social_rank,
            era_fit_score=self._era_score(text, dynasty),
            story_fit_score=self._story_score(text, social_rank),
            tags=self._tags_for(text, social_rank),
            is_valid=True,
            rejection_reason="",
        )

    def _validate_with_ai(
        self,
        *,
        dynasty: DynastyProfile,
        event: EventTemplate,
        text: str,
    ) -> PlayerIdentityValidationResponse | None:
        prompt = f"""你是历史悬疑游戏《史隙》的玩家身份校验器。只输出合法 JSON。

【朝代】{dynasty.name} / {dynasty.period_label}
【事件】{event.title}
【表层事件】{event.surface_event}
【禁止泄露】不能透露隐藏真相，不能赠送关键线索。
【玩家输入身份】{text}

判断这个身份是否适合当前历史剧本。合法身份只能影响称呼、语气、NPC 态度和背景介绍，不能改变主线真相、关键线索、推理正确性或结局判定。
现代国家元首、现代政党职位、现代科技职业、真实历史大人物本体、神仙外星人穿越者、带枪炮机器人等身份必须判为不合法。
如果合法，给出 normalized_name、display_name、social_rank、era_fit_score、story_fit_score、background_seed、warnings。
如果不合法，给出中文 rejection_reason 和 3 个中文 suggestions。
"""
        ai_response = self.ai_client.generate_json_sync(
            module="PlayerIdentityValidator",
            prompt=prompt,
            schema_hint=IDENTITY_SCHEMA_HINT,
        )
        if not ai_response.success:
            return None

        payload = ai_response.parsed_json
        if not payload.get("is_valid"):
            return PlayerIdentityValidationResponse(
                is_valid=False,
                rejection_reason=str(payload.get("rejection_reason") or "这个身份不适合当前历史剧本，会破坏时代背景。"),
                suggestions=self._safe_suggestions(payload.get("suggestions")),
                warnings=self._string_list(payload.get("warnings")),
            )

        display_name = self._clean_text(str(payload.get("display_name") or text))
        rejection = self._rule_rejection(display_name, dynasty=dynasty)
        if rejection:
            return PlayerIdentityValidationResponse(is_valid=False, rejection_reason=rejection, suggestions=self.default_suggestions())

        social_rank = str(payload.get("social_rank") or self._rank_for(display_name))
        if social_rank not in {"low", "middle", "high"}:
            social_rank = self._rank_for(display_name)
        normalized_name = self._clean_text(str(payload.get("normalized_name") or self._normalized_name(display_name, social_rank)))
        seed = str(payload.get("background_seed") or "")
        identity = PlayerIdentity(
            identity_id=f"custom_{abs(hash(display_name)) % 10_000_000}",
            source="custom",
            display_name=display_name,
            normalized_name=normalized_name,
            description=self._description_for(display_name=display_name, social_rank=social_rank),
            background=self._background_from_seed(display_name=display_name, seed=seed, social_rank=social_rank, event=event),
            social_rank=social_rank,  # type: ignore[arg-type]
            era_fit_score=self._score(payload.get("era_fit_score"), default=self._era_score(display_name, dynasty)),
            story_fit_score=self._score(payload.get("story_fit_score"), default=self._story_score(display_name, social_rank)),
            tags=self._tags_for(display_name, social_rank),
            is_valid=True,
            rejection_reason="",
        )
        return PlayerIdentityValidationResponse(
            is_valid=True,
            identity=identity,
            warnings=self._string_list(payload.get("warnings")),
        )

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", "", value.strip())

    def _rule_rejection(self, text: str, *, dynasty: DynastyProfile) -> str:
        if not text:
            return "请先输入一个身份。"
        if len(text) < 2:
            return "这个身份太短，请换成时代内可存在的身份。"
        if len(text) > 18:
            return "这个身份太长，请换成更简短、清楚的身份。"
        if not re.search(r"[\u4e00-\u9fff]", text):
            return "这个身份需要使用中文，并且适合当前历史剧本。"
        if re.search(r"[A-Za-z]{2,}", text):
            return "这个身份暂时不适合当前剧本，请避免英文、指令或现代身份。"
        if re.fullmatch(r"[\W_]+", text):
            return "这个身份无法识别，请换成时代内可存在的身份。"

        term_groups = [
            self.modern_political_terms,
            self.modern_job_terms,
            self.historical_person_terms,
            self.world_breaking_terms,
            self.injection_terms,
            set(dynasty.forbidden_terms),
        ]
        for terms in term_groups:
            for term in terms:
                if term and term.lower() in text.lower():
                    return "这个身份暂时不适合当前剧本，请换成时代内可存在、不会压过主线的身份，例如书生、樵夫、游方探事人。"
        return ""

    def _rank_for(self, text: str) -> str:
        if any(term in text for term in ["宰相", "高官", "尚书", "侍郎", "巡抚", "知府", "贵族", "侯府", "官员"]):
            return "high"
        if any(term in text for term in ["乞丐", "樵夫", "农夫", "小贩", "伙计", "仆", "脚夫", "更夫"]):
            return "low"
        return "middle"

    def _normalized_name(self, text: str, social_rank: str) -> str:
        if "侦探" in text:
            return text.replace("侦探", "探事人")
        if "樵夫" in text:
            return "近郊樵夫"
        if "书生" in text:
            return "寄居书生"
        if "宰相" in text:
            return "来访高官"
        if social_rank == "high":
            return "有名望的来访者"
        if social_rank == "low":
            return "城中低微行当人"
        return text

    def _description_for(self, *, display_name: str, social_rank: str) -> str:
        if social_rank == "high":
            return f"{display_name}有名望或权势，容易让人谨慎，却不能压过证据与主线。"
        if social_rank == "low":
            return f"{display_name}地位低微，行动不起眼，也更容易被轻慢和怀疑。"
        return f"{display_name}能自然查访人情，但仍需要靠证据逐步取信。"

    def _background_for(self, *, display_name: str, normalized_name: str, social_rank: str, event: EventTemplate) -> str:
        if social_rank == "high":
            return (
                f"你自称是{display_name}，因旧书、文稿或故人邀约来到书坊附近。雨夜火起后，众人虽不敢轻慢你，"
                f"却也更怕牵连官面责任；你仍只能凭证据靠近这场{event.title}。"
            )
        if social_rank == "low":
            return (
                f"你自称是{display_name}，为生计在书坊周边奔走。雨夜经过后巷时，你原只想避雨或讨口热水，"
                f"却被火光和封门声卷入{event.title}，旁人的眼神先带着怀疑。"
            )
        return (
            f"你自称是{display_name}，以{normalized_name}的名头在城中行走。雨夜来到书坊附近时，你本为访人问事，"
            f"却被后院火光与差役封门卷入{event.title}。"
        )

    def _background_from_seed(self, *, display_name: str, seed: str, social_rank: str, event: EventTemplate) -> str:
        cleaned_seed = self._clean_visible_sentence(seed)
        if 24 <= len(cleaned_seed) <= 96 and not self._contains_forbidden_visible(cleaned_seed):
            return f"你自称是{display_name}，{cleaned_seed}雨夜火起后，你被封门声留在书坊附近，只能凭眼前证据靠近这场{event.title}。"
        return self._background_for(display_name=display_name, normalized_name=display_name, social_rank=social_rank, event=event)

    def _clean_visible_sentence(self, text: str) -> str:
        return re.sub(r"\s+", "", text.strip("。；; "))

    def _contains_forbidden_visible(self, text: str) -> bool:
        forbidden = self.modern_political_terms | self.modern_job_terms | self.historical_person_terms | self.world_breaking_terms | self.injection_terms
        return any(term and term in text for term in forbidden)

    def _tags_for(self, text: str, social_rank: str) -> list[str]:
        tags = {
            "low": ["低身份", "易被轻慢"],
            "middle": ["中身份", "可查访"],
            "high": ["高身份", "受忌惮"],
        }[social_rank]
        if "书" in text or "生" in text:
            tags.append("读书人")
        if "侦探" in text or "探事" in text:
            tags.append("查案")
        if "樵夫" in text:
            tags.append("后巷")
        return tags

    def _era_score(self, text: str, dynasty: DynastyProfile) -> float:
        if any(term in text for term in ["宰相", "高官", "贵族"]):
            return 0.72
        if any(term in text for term in ["侦探"]):
            return 0.76
        return 0.9 if dynasty.dynasty_id == "ming" else 0.78

    def _story_score(self, text: str, social_rank: str) -> float:
        if social_rank == "high":
            return 0.66
        if any(term in text for term in ["书生", "侦探", "探事", "郎中", "樵夫"]):
            return 0.82
        return 0.72

    def _background_from_json(self, payload: dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False)

    def _score(self, value: Any, *, default: float) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return default
        return max(0.0, min(1.0, number))

    def _safe_suggestions(self, value: Any) -> list[str]:
        suggestions = self._string_list(value)
        return suggestions[:3] if suggestions else self.default_suggestions()

    def _string_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    def _can_use_ai(self) -> bool:
        return (
            not self.settings.use_mock_ai
            and self.settings.ai_provider == "deepseek"
            and self.settings.deepseek_api_key_available
        )


player_identity_service = PlayerIdentityService()

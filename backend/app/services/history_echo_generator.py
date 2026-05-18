from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from app.core.config import Settings, settings
from app.models.game_models import ChoiceCard, Clue, EndingRule, GameState, NPCProfile
from app.services.ai_client import AIClient


@dataclass(frozen=True)
class HistoryEchoResult:
    text: str
    sources: list[str]
    ai_success: bool
    fallback_used: bool
    error_message: str | None = None


class HistoryEchoGenerator:
    def __init__(self, *, ai_client: AIClient | None = None, runtime_settings: Settings | None = None) -> None:
        self.settings = runtime_settings or settings
        self.ai_client = ai_client or AIClient(self.settings)
        self.prompt_path = Path(__file__).resolve().parents[2] / "data" / "prompts" / "history_echo.md"

    def generate(
        self,
        *,
        ending: EndingRule,
        state: GameState,
        choices: dict[str, ChoiceCard],
        clues: dict[str, Clue],
        npcs: dict[str, NPCProfile],
        template_echo: str,
    ) -> HistoryEchoResult:
        choice = choices.get(state.final_choice_id or "")
        choice_title = choice.title if choice else "未记录最终选择"
        clue_titles = self._related_clue_titles(ending=ending, state=state, clues=clues)
        npc_fate_summaries = self._npc_fate_summaries(ending=ending, npcs=npcs)
        sources = self._sources(choice_title=choice_title, clue_titles=clue_titles, npc_fate_summaries=npc_fate_summaries)
        fallback_text = self._fallback_echo(
            ending=ending,
            choice_title=choice_title,
            clue_titles=clue_titles,
            npc_fate_summaries=npc_fate_summaries,
            template_echo=template_echo,
        )

        ai_response = self.ai_client.generate_json_sync(
            module="HistoryEchoGenerator",
            prompt=self._build_prompt(
                ending=ending,
                state=state,
                choice_title=choice_title,
                clue_titles=clue_titles,
                npc_fate_summaries=npc_fate_summaries,
                fallback_text=fallback_text,
            ),
            schema_hint={"history_echo": "中文历史回声字符串"},
        )
        if ai_response.success:
            text = str(ai_response.parsed_json.get("history_echo", "")).strip()
            if self._is_valid_echo(
                text,
                choice_title=choice_title,
                clue_titles=clue_titles,
                npc_fate_summaries=npc_fate_summaries,
            ):
                return HistoryEchoResult(text=text, sources=sources, ai_success=True, fallback_used=False)

        return HistoryEchoResult(

            text=fallback_text,
            sources=sources,
            ai_success=False,
            fallback_used=True,
            error_message=ai_response.error_message,
        )

    def _related_clue_titles(self, *, ending: EndingRule, state: GameState, clues: dict[str, Clue]) -> list[str]:
        ordered_ids: list[str] = []
        for clue_id in ending.related_clue_ids + state.discovered_clue_ids:
            if clue_id in clues and clue_id not in ordered_ids:
                ordered_ids.append(clue_id)
        return [clues[clue_id].title for clue_id in ordered_ids[:3]]

    def _npc_fate_summaries(self, *, ending: EndingRule, npcs: dict[str, NPCProfile]) -> list[str]:
        summaries: list[str] = []
        for npc_id, fate in list(ending.npc_fates.items())[:3]:
            npc_name = npcs.get(npc_id).name if npc_id in npcs else npc_id
            summaries.append(f"{npc_name}：{fate}")
        return summaries

    def _sources(self, *, choice_title: str, clue_titles: list[str], npc_fate_summaries: list[str]) -> list[str]:
        sources = [f"最终选择：{choice_title}"]
        sources.extend(f"关键线索：{title}" for title in clue_titles[:3])
        sources.extend(f"人物命运：{summary}" for summary in npc_fate_summaries[:2])
        return sources

    def _fallback_echo(
        self,
        *,
        ending: EndingRule,
        choice_title: str,
        clue_titles: list[str],
        npc_fate_summaries: list[str],
        template_echo: str,
    ) -> str:
        clue_part = "、".join(clue_titles[:2]) if clue_titles else "那些未能说出口的证据"
        fate_part = "；".join(npc_fate_summaries[:2]) if npc_fate_summaries else "众人的去向仍被火案牵连"
        base_echo = template_echo or ending.history_echo
        return (
            f"你选择「{choice_title}」之后，「{clue_part}」不再只是案卷里的物证，"
            f"也成了衡量真相能否留下的分界。{fate_part}。"
            f"火案的表层结果已经落定，但书坊、封口令与粮册背后的时代压力并未因此消失。"
            f"{base_echo}"
        )

    def _build_prompt(
        self,
        *,
        ending: EndingRule,
        state: GameState,
        choice_title: str,
        clue_titles: list[str],
        npc_fate_summaries: list[str],
        fallback_text: str,
    ) -> str:
        template = self.prompt_path.read_text(encoding="utf-8") if self.prompt_path.exists() else ""
        return f"""{template}

【硬性规则】
- 只输出 JSON 对象。
- 只能输出字段 history_echo。
- 不得输出、修改或暗示新的 ending_id。
- 不得改变结局判定，不得新增线索，不得剧透未在上下文中的幕后身份。
- 用户可见文本必须全中文。

【已由后端规则判定的结局】
结局 ID：{ending.ending_id}
结局标题：{ending.title}
结局摘要：{ending.result_summary}
最终选择：{choice_title}
玩家分数：truth={state.scores.truth}, order={state.scores.order}, survival={state.scores.survival}, risk={state.risk_level}
关键线索：{'、'.join(clue_titles) if clue_titles else '无'}
人物命运：{'；'.join(npc_fate_summaries) if npc_fate_summaries else '无'}
本地 fallback：{fallback_text}

请生成一句到三句中文历史回声，必须引用最终选择、至少两条关键线索或两名人物命运中的信息。
"""

    def _is_valid_echo(
        self,
        text: str,
        *,
        choice_title: str,
        clue_titles: list[str],
        npc_fate_summaries: list[str],
    ) -> bool:
        if not text:
            return False
        if len(text) < 20:
            return False
        if re.search(r"[A-Za-z]{4,}", text):
            return False
        if not re.search(r"[\u4e00-\u9fff]", text):
            return False

        references = 0
        if choice_title and choice_title != "未记录最终选择" and choice_title in text:
            references += 1
        references += sum(1 for title in clue_titles if title and title in text)
        npc_names = [summary.split("：", 1)[0] for summary in npc_fate_summaries if "：" in summary]
        references += sum(1 for name in npc_names if name and name in text)
        structural_terms = ["火案", "书坊", "封口令", "粮册", "时代压力"]
        if any(term in text for term in structural_terms):
            references += 1
        return references >= 2


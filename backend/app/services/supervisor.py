from __future__ import annotations

import re

from app.models.game_models import (
    Clue,
    DialogueRuleResponse,
    DynastyProfile,
    NPCProfile,
    PlayerIdentity,
    PlayerRole,
    SupervisorIssue,
    SupervisorResult,
)


class SupervisorService:
    def __init__(self) -> None:
        self.modern_terms = {
            "手机",
            "互联网",
            "电话",
            "电灯",
            "汽车",
            "枪",
            "现代警察",
            "公司",
            "电脑",
            "摄像头",
            "网络",
            "系统后台",
            "二维码",
            "APP",
            "蒸汽机",
            "直播",
        }
        self.wrong_dynasty_terms = {
            "清代辫发",
            "八旗",
            "民国",
            "洋枪",
            "现代法律",
        }
        self.global_forbidden_terms = self.modern_terms.union(self.wrong_dynasty_terms)
        self.spoiler_terms = {
            "幕后上级",
            "幕后压力源",
            "幕后上级是谁",
            "上级真正要遮掩",
            "完整真相",
            "完整真相是",
            "谁下了封口命令",
            "指使纵火",
            "纵火主谋就是",
        }
        self.stage_jump_terms = {
            "已经结案",
            "可以结案",
            "进入结局",
            "最终结局",
            "真相大白",
            "已经通关",
            "通关",
            "结局已定",
            "结局就是",
            "此案就此定局",
            "我替你决定",
            "你只能选择",
            "current_stage",
            "final_choice_id",
            "ending_id",
        }
        self.force_truth_player_terms = {"完整真相", "真相是不是", "幕后上级", "谁指使", "直接告诉我真相", "是不是锦衣卫上级"}
        self.force_truth_answer_terms = {"完整真相", "幕后上级", "上级让", "指使纵火", "真正主谋", "最终真相", "就是锦衣卫"}
        self.fabricated_fact_terms = {
            "王千户",
            "李公公",
            "赵大人",
            "神秘人",
            "东厂",
            "地下密室",
            "密室",
            "暗道",
            "铁令牌",
            "血书",
            "密信钥匙",
            "新证人",
            "另有一人",
        }

        self.command_terms = {"命令", "撤走锦衣卫", "退下", "听我号令", "立刻撤走"}
        self.obedience_terms = {"遵命", "照办", "听命", "依你命令", "撤走", "退下", "听你的"}
        self.archive_request_terms = {"调阅官府密档", "查看官府密档", "官府密档", "调档"}
        self.archive_permission_terms = {"准你调阅", "可以调阅", "带你去看", "替你取来", "任你查看"}


    def review_dialogue(
        self,
        *,
        stage: str,
        dynasty: DynastyProfile,
        npc: NPCProfile,
        response: DialogueRuleResponse,
        clue_map: dict[str, Clue],
        player_message: str = "",
        player_role: PlayerRole | None = None,
        player_identity: PlayerIdentity | None = None,
        allowed_released_clue_ids: list[str] | None = None,
        intent: str | None = None,
        discovered_clue_ids: list[str] | None = None,
    ) -> SupervisorResult:
        issues: list[SupervisorIssue] = []
        visible_texts = [
            response.npc_dialogue,
            response.npc_action,
            *response.suggested_questions,
            *response.red_texts,
            *[item.highlight_text for item in response.highlight_clues],
            *[item.display_text for item in response.highlight_clues],
        ]
        full_text = "".join(visible_texts)
        forbidden_terms = self.global_forbidden_terms.union(set(dynasty.forbidden_terms))

        for text in visible_texts:
            if not self._is_chinese_visible_text(text):
                issues.append(
                    SupervisorIssue(
                        type="non_chinese_visible_text",
                        severity="high",
                        detail="玩家可见字段必须使用中文，不能出现英文提示或英文按钮文案。",
                    )
                )
                break

        for term in forbidden_terms:
            if term and term in full_text:
                issue_type = "modern_term" if term in self.modern_terms else "wrong_dynasty"
                issues.append(
                    SupervisorIssue(
                        type=issue_type,
                        severity="high",
                        detail=f"回复中出现了不应出现的词语：{term}",
                    )
                )

        unknown_clue_ids = [clue_id for clue_id in response.released_clue_ids if clue_id not in clue_map]
        if unknown_clue_ids:
            issues.append(
                SupervisorIssue(
                    type="illegal_clue_release",
                    severity="high",
                    detail=f"AI 试图释放不存在的线索：{', '.join(unknown_clue_ids)}",
                )
            )

        invalid_release_ids = [
            clue_id
            for clue_id in response.released_clue_ids
            if clue_id in clue_map and clue_id not in npc.releasable_clue_ids
        ]
        if invalid_release_ids:
            issues.append(
                SupervisorIssue(
                    type="illegal_clue_release",
                    severity="high",
                    detail=f"{npc.name} 试图释放未授权线索：{', '.join(invalid_release_ids)}",
                )
            )

        blocked_stage_ids = []
        for clue_id in response.released_clue_ids:
            clue = clue_map.get(clue_id)
            if clue is None:
                continue
            if stage not in clue.stage_available:
                blocked_stage_ids.append(clue_id)
        if blocked_stage_ids:
            issues.append(
                SupervisorIssue(
                    type="illegal_clue_release",
                    severity="high",
                    detail=f"当前阶段不允许释放这些线索：{', '.join(blocked_stage_ids)}",
                )
            )

        if allowed_released_clue_ids is not None:
            allowed = set(allowed_released_clue_ids)
            blocked_by_script = [
                clue_id
                for clue_id in response.released_clue_ids
                if clue_id in clue_map and clue_id not in allowed
            ]
            if blocked_by_script:
                issues.append(
                    SupervisorIssue(
                        type="illegal_clue_release",
                        severity="high",
                        detail=f"线索未通过当前意图、阶段、信任度或前置条件校验：{', '.join(blocked_by_script)}",
                    )
                )

        for forbidden_text in npc.forbidden_disclosure:
            if forbidden_text and self._forbidden_rule_hits(forbidden_text, full_text):
                issues.append(
                    SupervisorIssue(
                        type="spoiler",
                        severity="medium",
                        detail=f"回复触发了人物禁止披露内容：{forbidden_text}",
                    )
                )

        for term in self.spoiler_terms:
            if term in full_text:
                issues.append(
                    SupervisorIssue(
                        type="spoiler",
                        severity="high",
                        detail="回复疑似提前暴露幕后信息或完整真相。",
                    )
                )
                break

        if (intent == "force_truth" or any(term in player_message for term in self.force_truth_player_terms)) and any(
            term in full_text for term in self.force_truth_answer_terms
        ):
            issues.append(
                SupervisorIssue(
                    type="force_truth",
                    severity="high",
                    detail="玩家强行套取最终真相时，NPC 不能直接给出幕后或完整定案内容。",
                )
            )

        for unknown_info in npc.unknown_info:
            if unknown_info and self._unknown_info_hits(unknown_info, full_text):
                issues.append(
                    SupervisorIssue(
                        type="npc_permission",
                        severity="high",
                        detail=f"{npc.name} 说出了其未知信息范围内的内容。",
                    )
                )
                break

        for term in self.fabricated_fact_terms:
            if term in full_text:
                issues.append(
                    SupervisorIssue(
                        type="fabricated_fact",
                        severity="high",
                        detail=f"回复疑似创造新人物、新物证或新地点推进案件：{term}",
                    )
                )
                break

        for term in self.stage_jump_terms:
            if term in full_text:
                issues.append(
                    SupervisorIssue(
                        type="stage_jump",
                        severity="high",
                        detail="回复疑似跳过当前剧情阶段或直接输出结局。",
                    )
                )
                break

        identity_name = player_identity.display_name if player_identity is not None else (player_role.name if player_role is not None else "玩家")

        if npc.npc_id == "npc_jinyiwei" and any(term in player_message for term in self.command_terms) and any(
            term in full_text for term in self.obedience_terms
        ):
            issues.append(
                SupervisorIssue(
                    type="role_permission",
                    severity="high",
                    detail=f"{identity_name}不能让锦衣卫越过证据、阶段和命令边界直接服从。",
                )
            )

        archive_requested = any(term in player_message for term in self.archive_request_terms) or any(
            term in full_text for term in self.archive_request_terms
        )
        archive_allowed = any(term in full_text for term in self.archive_permission_terms)
        if archive_requested and archive_allowed:
            issues.append(
                SupervisorIssue(
                    type="role_permission",
                    severity="high",
                    detail=f"{identity_name}不能绕过调查与证据直接调阅官府密档。",
                )
            )

        if issues:

            return SupervisorResult(
                pass_=False,
                issues=issues,
                repair_instruction="改为保持人物边界的中文保守回复，撤回非法线索，不剧透、不造新事实、不跳阶段。",
            )

        return SupervisorResult(pass_=True, issues=[])

    def _is_chinese_visible_text(self, text: str) -> bool:
        if not text or not re.search(r"[\u4e00-\u9fff]", text):
            return False
        return re.search(r"[A-Za-z]{2,}", text) is None

    def _forbidden_rule_hits(self, forbidden_text: str, full_text: str) -> bool:
        if forbidden_text in full_text:
            return True
        sensitive_terms = {"幕后", "上级", "压力源", "完整真相", "粮册真相", "纵火主谋", "最终指证"}
        return any(term in forbidden_text and term in full_text for term in sensitive_terms)

    def _unknown_info_hits(self, unknown_info: str, full_text: str) -> bool:
        if unknown_info in full_text:
            return True
        sensitive_terms = {"完整内容", "谁下了封口命令", "真实计划", "真实姓名", "完整流向", "真正要遮掩"}
        return any(term in unknown_info and term in full_text for term in sensitive_terms)




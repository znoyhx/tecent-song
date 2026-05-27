from __future__ import annotations


ABSTRACT_CLUE_TOKENS = (
    "时间线",
    "时间轴",
    "时间表",
    "时间差",
    "动机",
    "疑点",
    "真相",
    "关系",
    "路线",
    "行动链",
    "证据链",
    "线索",
    "证言",
    "口供",
    "矛盾",
    "嫌疑",
    "阴谋",
    "漏洞",
    "推断",
    "判断",
)

PUNCTUATION_STRIP = " \t\r\n「」『』《》[]【】()（）:：-—_、，。,.；;"


def is_abstract_clue_title(title: str) -> bool:
    compact = "".join(str(title or "").split()).strip(PUNCTUATION_STRIP)
    if not compact:
        return True
    if compact in ABSTRACT_CLUE_TOKENS:
        return True
    return any(token in compact for token in ABSTRACT_CLUE_TOKENS)


def concrete_clue_title(title: str, *, index: int = 0, keyword: str = "", location_name: str = "") -> str:
    clean = str(title or "").strip().strip(PUNCTUATION_STRIP)
    if clean and not is_abstract_clue_title(clean):
        return clean

    subject = _extract_subject(clean) or str(keyword or "").strip() or str(location_name or "").strip()
    subject = _clean_subject_name(subject) or "现场"

    if any(token in clean for token in ("证言", "口供")):
        return f"{subject}口供记录"
    if any(token in clean for token in ("时间线", "时间轴", "时间表", "时间差")):
        return f"{subject}更筹铜签"
    if any(token in clean for token in ("路线", "行动链")):
        return f"{subject}车辙泥印"
    if "动机" in clean:
        return f"{subject}私账残页"
    if any(token in clean for token in ("关系", "矛盾")):
        return f"{subject}往来封签"
    if any(token in clean for token in ("真相", "疑点", "嫌疑", "阴谋", "漏洞", "推断", "判断", "证据链", "线索")):
        return f"{subject}物证残片"

    fallback_objects = ("封泥残片", "更筹铜签", "车辙泥印", "私账残页", "往来封签", "绳结断口")
    return fallback_objects[index % len(fallback_objects)]


def concrete_clue_visual_subject(title: str, *, index: int = 0, keyword: str = "", location_name: str = "") -> str:
    concrete = concrete_clue_title(title, index=index, keyword=keyword, location_name=location_name)
    if concrete == title:
        return concrete
    return f"{concrete}（用于表现抽象线索“{title}”的具体可见物证）"


def scene_clue_visual_requirement(clue, *, index: int = 0, location_name: str = "") -> str:
    title = _field(clue, "title")
    display_text = _field(clue, "display_text")
    detail = _field(clue, "detail")
    subject = concrete_clue_visual_subject(title, index=index, location_name=location_name)
    text = f"{title} {display_text} {detail}"
    requirements: list[str] = []

    if _has_any(text, "尸体", "尸身", "遗体", "死者"):
        requirements.append("画面中必须有尸体或覆布尸身，放在地面、榻上、担架或码头石面等合理位置，不能只画活人")
    if _has_any(text, "刀伤", "伤口", "致命伤"):
        requirements.append("刀伤必须表现为尸身衣物破口、胸前血迹或验尸痕迹，克制不血腥，不能只画一把刀")
    if _has_any(text, "空盒", "空木盒", "木盒"):
        requirements.append("必须有打开的空木盒，盒内空腔清楚可见")
    if _has_any(text, "暗格", "暗柜", "夹层", "抽屉"):
        requirements.append("必须有打开的暗格、暗柜或抽屉，与空盒或纸件在同一位置关系中")
    if _has_any(text, "密信", "信函", "草稿", "文书", "供词", "口供", "记录", "收据", "告示", "名单", "封口令"):
        requirements.append("必须有折叠、封缄、卷起或压在案上的纸本文书，绝对不能出现可读文字或乱码")
    if _has_any(text, "香囊", "荷包", "囊"):
        requirements.append("必须有布质香囊或小袋，靠近尸身腰间、证物盘或人物手边")
    if _has_any(text, "车辙", "脚印", "泥印", "足迹"):
        requirements.append("必须有泥地车辙、脚印或水痕，位于地面并能与热点位置对应")
    if _has_any(text, "血迹", "血"):
        requirements.append("必须有克制的血迹、擦痕或染色布料作为物证痕迹")
    if _has_any(text, "铜符", "鱼符", "腰牌", "符"):
        requirements.append("必须有磨损金属符牌或腰牌，靠近证物区")
    if _has_any(text, "酒", "茶", "药", "粉末"):
        requirements.append("必须使用宋代/唐代适配的陶杯、陶罐、漆盒、纸包或布包表现液体/粉末，不能用现代玻璃瓶或实验器皿")

    if not requirements:
        requirements.append("必须画成一个具体可见的物件或痕迹，材质、位置、遮挡关系清楚，不能只用标签或抽象概念")

    source_detail = detail or display_text or title
    place = f"在“{location_name}”中" if location_name else "在当前场景中"
    return (
        f"{subject}：{place}必须可见；"
        f"{'；'.join(requirements)}；"
        f"线索原始细节：{source_detail}"
    )


def _extract_subject(title: str) -> str:
    for separator in ("-", "—", "：", ":", "_"):
        if separator in title:
            tail = title.rsplit(separator, 1)[-1].strip(PUNCTUATION_STRIP)
            if tail and not is_abstract_clue_title(tail):
                return tail
            head = title.split(separator, 1)[0].strip(PUNCTUATION_STRIP)
            if head and not is_abstract_clue_title(head):
                return head
    for token in ABSTRACT_CLUE_TOKENS:
        title = title.replace(token, "")
    return _clean_subject_name(title)


def _clean_subject_name(value: str) -> str:
    subject = str(value or "").strip().strip(PUNCTUATION_STRIP)
    for token in ("的记录", "记录", "口供", "证言", "线索", "物证", "相关", "材料"):
        subject = subject.replace(token, "")
    return subject.strip(PUNCTUATION_STRIP)


def _field(item, name: str) -> str:
    if isinstance(item, dict):
        return str(item.get(name) or "")
    return str(getattr(item, name, "") or "")


def _has_any(text: str, *tokens: str) -> bool:
    return any(token in text for token in tokens)

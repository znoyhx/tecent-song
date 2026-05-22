from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


UNIFIED_STYLE_PROMPT = (
    "low-saturation Chinese historical suspense visual novel style, "
    "Ming dynasty bookshop mystery, dark cinematic lighting, rain night, "
    "fire glow, smoke, paper ash, muted ink wash texture mixed with digital painting, "
    "single coherent game scene, characters and environment generated together, "
    "same perspective, same lighting, no pasted character cutouts, "
    "consistent cast bible, same face and costume for the same named character across all images, "
    "no modern objects, no modern clothes, no neon, no western fantasy, no guns, "
    "no cars, no electricity, no anachronistic architecture, serious atmosphere, "
    "game background art, high detail, moody composition"
)

NEGATIVE_PROMPT = (
    "modern city, modern clothes, electric light, neon, car, gun, phone, "
    "western fantasy armor, anime school uniform, sci-fi, futuristic, bright cartoon, "
    "cute style, comedy, low quality, blurry, distorted, wrong dynasty, "
    "Qing dynasty queue hairstyle, Qing eight banners, Japanese samurai, modern police, "
    "Republican era clothes, English signs, gore, sexual content, "
    "pretty anime boy, childlike face, glossy idol portrait, inconsistent character face, "
    "question marks, ???, fake text, gibberish letters, unreadable Chinese characters, "
    "watermark, subtitle, label"
)

CHARACTER_STYLE_LOCKS = {
    "npc_worker": (
        "Character identity lock for A-Shen: the same 22-26 year old Han Chinese Ming dynasty "
        "woodblock engraver in every scene and portrait; slim but adult, narrow shoulders, "
        "rough artisan face, tired anxious eyes, short messy black hair tied with a plain cloth, "
        "plain dark indigo-gray short worker robe, rolled sleeves, ink stains on cuffs and fingertips, "
        "small carving-knife pouch, nervous guarded posture, not a child, not a pretty anime idol, "
        "not modern hair, not a clean scholar robe."
    ),
    "npc_owner": (
        "Character identity lock for Xu the bookshop owner: the same middle-aged Han Chinese Ming "
        "bookshop owner in every scene and portrait; weathered cautious face, graying hair, "
        "plain worn dark robe, paper ash and ink on cuffs, guarded merchant-scholar posture."
    ),
    "npc_scholar": (
        "Character identity lock for Gu Wen: the same thin failed Ming scholar in every scene and portrait; "
        "worn damp robe, anxious stubborn eyes, protective hold on manuscript papers, no official costume."
    ),
    "npc_jinyiwei": (
        "Character identity lock for Lu Zheng: the same low-ranking Ming Jinyiwei officer in every scene and portrait; "
        "restrained stern face, practical dark official uniform, not a grand commander, no fantasy armor."
    ),
}

CLUE_PROMPT_SUFFIX = (
    "object-focused clue illustration, no visible text, no letters, no question marks, "
    "no unreadable marks, no watermark, no UI icons"
)


SCENE_TITLES = {
    "scene_front_hall": "书坊前厅",
    "scene_account_room": "账房暗格",
    "scene_fire_yard": "书坊后院火场",
    "scene_lamp_shelf": "灯油架旁",
    "scene_engraving_room": "烧毁的刻版间",
    "scene_back_gate": "后门雨泥处",
    "scene_rain_alley": "雨巷",
    "scene_city_gate": "城门搜检口",
    "scene_interrogation_room": "锦衣卫临时问话处",
}

SCENE_BLUEPRINTS = {
    "scene_front_hall": (
        "明代应天府雨夜书坊前厅，画面中要同时出现许掌柜与书坊空间。"
        "场景包含木柜台、账簿桌、靠墙书柜、层叠书架、旧书箱、门柱刻痕、潮湿地面和被烟熏暗的油灯。"
        "许掌柜站在柜台后或柜台侧，中年书坊掌柜，疲惫、谨慎、袖口有纸灰墨痕，手压账册。"
    ),
    "scene_account_room": (
        "狭小账房暗格，许掌柜在窄桌旁守着账册，神情防备。"
        "场景包含账册、被刮薄的账行、暗抽屉锁眼、新木屑、订金小票、墙角二次纸灰和低矮油灯。"
    ),
    "scene_fire_yard": (
        "雨后的书坊后院火场，无主要 NPC 占据画面，重点给可调查物件留出清晰位置。"
        "场景包含灰烬堆、旧书箱底部焦圈、偏离灯油架的深焦痕、未被挪动的救火水桶、湿石地与残余火光。"
    ),
    "scene_lamp_shelf": (
        "书坊墙根灯油架旁，无主要 NPC 占据画面。"
        "场景包含半倒未倒的灯油架、油罐、异常火油痕、雨水脚印、被拖动过的灯架痕迹和通往后门的湿脚印。"
    ),
    "scene_engraving_room": (
        "烧毁的刻版间，阿沈与刻版桌、后门一起生成在同一画面。"
        "阿沈是年轻明代刻工，瘦削胆怯，袖口和指缝有旧墨，站在刻版桌旁并下意识看向后门。"
        "场景包含木屑、残墨、刻刀、替换过的新刻版、松动后门门闩、残墨布和焦黑木板。"
    ),
    "scene_back_gate": (
        "书坊后门雨泥处，阿沈靠近门槛或墙根，人物与雨泥、门闩处于同一透视。"
        "场景包含后门门闩内侧新磨痕、外出又折返的泥印、墙根细纸线、窄门洞、湿木门和雨夜青石地。"
    ),
    "scene_rain_alley": (
        "明代雨巷，顾闻在巷口暗处来回踱步，与墙面告示和城门方向的雨泥同画面生成。"
        "顾闻是清瘦落第士子，焦急执拗，旧袍下摆沾着黄泥，怀中护着受潮诗稿。"
        "场景包含搜检告示、湿墙、伞影、黄泥衣摆、晚来客记忆的门外阴影和远处更鼓灯火。"
    ),
    "scene_city_gate": (
        "雨夜城门搜检口，顾闻站在可疑纸包与告示附近，人物和守门火把处在同一光源中。"
        "场景包含二次搜检告示、城门火把、守门人、纸包书箱、诗稿外皮折角和粮册术语相关的官样文书氛围。"
    ),
    "scene_interrogation_room": (
        "锦衣卫临时问话处，陆峥与木案、封条和薄纸一起生成在压迫感画面中。"
        "陆峥是低阶锦衣卫校尉，冷峻克制、深色便于行动的官面服色，手压薄纸并站在门边形成阻隔。"
        "场景包含未盖完印的封条、命令旁注、临时问话记录、半张搜检名单、湿封条、木案和低烛光。"
    ),
}

NPC_TITLES = {
    "npc_owner": "许掌柜",
    "npc_worker": "阿沈",
    "npc_scholar": "顾闻",
    "npc_jinyiwei": "陆峥",
}

NPC_SCENE_DESCRIPTIONS = {
    "npc_owner": "许掌柜，中年明代书坊掌柜，谨慎疲惫，精明但心虚，穿半旧深色长衫，袖口有纸灰与墨痕。",
    "npc_worker": "阿沈，年轻明代刻工，瘦削胆怯，简单工服，袖口和指缝有旧墨，常回避后门方向。",
    "npc_scholar": "顾闻，清瘦落第士子，旧袍受潮，下摆沾黄泥，怀中护着诗稿，焦急又执拗。",
    "npc_jinyiwei": "陆峥，低阶锦衣卫校尉，深色官面服色，冷峻克制，奉命封锁但眼神有迟疑。",
}

HOTSPOT_VISUAL_HINTS = {
    "ledger_desk": "账簿桌上有缺口整齐的稿单，位于玩家容易点击的前景或中景",
    "old_box": "旧书箱缝隙露出半枚朱红纸角，靠近书柜和书架下方",
    "apprentice_watch": "门柱内侧有守夜更签刻痕，靠近前厅入口",
    "torn_ledger_line": "账册中被刮去的一行留下发白薄痕",
    "deposit_receipt": "订金小票被水汽泡皱，夹在账册或桌角",
    "locked_inner_drawer": "暗抽屉锁眼旁有新木屑",
    "account_ash": "账房角落有一小撮较新的纸灰",
    "ash_pile": "灰烬堆里露出烧焦残页",
    "char_mark": "最深焦黑偏离灯油架，靠近墙根旧箱",
    "scorched_box_bottom": "旧书箱底部形成明显焦圈",
    "fire_bucket": "救火水桶摆得过于整齐，水面几乎无泼洒痕",
    "oil_jar": "油罐旁有异常重的火油痕",
    "rain_tracks": "雨水脚印从后门方向断续延伸",
    "moved_lamp_stand": "灯架拖痕朝旧书箱方向偏移",
    "back_door": "刻版间后门门闩有新划痕",
    "carved_board": "一块刻版边角颜色过新",
    "ink_rag": "残墨布与阿沈袖口旧墨相互呼应",
    "mud_scrape": "后门外有外出又折返的泥印",
    "gate_latch": "门闩内侧磨痕比外侧更新",
    "hidden_thread": "墙根挂着极细纸线",
    "search_notice": "雨巷墙上贴着被雨水洗开的搜检告示",
    "muddy_hem": "顾闻衣摆沾着城门外常见黄泥",
    "late_visitor_memory": "门外暗处有晚来客记忆般的模糊雨影",
    "second_notice": "城门处有二次搜检告示，纸面不可出现可读文字",
    "grain_term": "官样告示与粮册文书氛围突出，但不写真实文字",
    "outer_wrapper": "顾闻怀中诗稿外皮有明显折角",
    "sealed_desk": "木案上有未盖完印的封条和红印痕",
    "order_conflict_note": "命令旁注以纸张位置和封口形态表达，不出现可读文字",
    "temp_record": "临时问话记录压在木案一侧，纸面不可读",
    "search_list": "半张搜检名单露出折痕和圈点形态，不能有可读文字",
}

CLUE_VISUAL_HINTS = {
    "clue_missing_manuscript_list": "缺失稿单：账簿页边缺口整齐，像火前被刻意撕走一行",
    "clue_red_seal": "半枚朱红纸角：旧书箱缝隙里夹着红印纸角",
    "clue_apprentice_watch_mark": "守夜更签刻痕：门柱内侧细小刻痕",
    "clue_ledger_line_erased": "被刮去的账目：账册上发白的刮痕",
    "clue_deposit_receipt": "旧稿订金小票：水汽泡皱的小票",
    "clue_locked_inner_drawer": "暗抽屉新木屑：锁眼边新鲜木屑",
    "clue_account_room_ash": "账房二次纸灰：角落一小撮新灰",
    "clue_burned_page": "烧焦残页：灰烬里露出残纸与烧痕",
    "clue_fire_origin_wrong": "起火点异常：最深焦黑不在灯油架旁",
    "clue_scorched_box_bottom": "旧箱底部焦圈：箱底被火先咬住的圆形焦痕",
    "clue_fire_bucket_unused": "未动的救火水桶：水桶过于整齐",
    "clue_oil_smell": "异常火油味：墙根湿石上的深色油迹",
    "clue_rainwater_tracks": "雨水脚印：后门方向进入的湿脚印",
    "clue_backdoor_latch": "后门门闩松动：新划痕和松动门闩",
    "clue_carved_board_replaced": "替换过的刻版：边角颜色过新的木版",
    "clue_ink_on_sleeve": "袖口旧墨：残墨布与袖口墨痕呼应",
    "clue_worker_back_gate_trip": "阿沈后门往返：外出又折返的泥印",
    "clue_hidden_page_thread": "夹页装订纸线：墙根极细纸线",
    "clue_city_gate_search": "搜检告示：被雨水洗开的告示轮廓",
    "clue_scholar_muddy_hem": "顾闻衣摆黄泥：旧袍下摆的黄泥",
    "clue_memory_late_visitor": "晚来客回忆：门外避雨的暗影",
    "clue_city_gate_second_notice": "二次搜检告示：新贴告示与旧雨痕并存",
    "clue_grain_term_mismatch": "粮册术语不合常理：官样文书气氛被突出但不出现文字",
    "clue_scholar_outer_wrapper": "诗稿外皮折角：外皮折角与装订纸线呼应",
    "clue_jinyiwei_gag_order": "锦衣卫封口令：未盖完印的封条和薄纸",
    "clue_lu_order_conflict": "陆峥命令矛盾：命令旁注以压纸和封口姿态表现",
    "clue_temp_interrogation_record": "临时问话记录：木案上的问话纸张顺序",
    "clue_lu_search_list": "陆峥搜检名单：半张名单折痕与圈点形态",
    "clue_gag_order_wording": "封口令措辞：封条背面小字以不可读纹理表现",
}



@dataclass(frozen=True)
class VisualAssetPrompt:
    asset_id: str
    category: str
    title: str
    prompt: str
    negative_prompt: str = NEGATIVE_PROMPT
    image_size: str = "1024x1024"


class VisualPromptAgent:
    """Deterministic prompt catalog for the Ming bookshop demo visuals."""

    def __init__(self) -> None:
        self.assets = self._build_assets()
        self.aliases = {
            "scene_bookshop_fire_yard": "scene_bookshop_backyard_fire",
            "scene_bookshop_engraving_room": "scene_burned_printing_room",
            "scene_interrogation_room": "scene_jinyiwei_interrogation",
            "npc_owner_xu": "npc_xu_owner",
            "npc_worker_ashen": "npc_ashen_worker",
            "npc_scholar_guwen": "npc_guwen_scholar",
            "npc_jinyiwei_lu": "npc_luzheng_jinyiwei",
        }

    def normalize_asset_id(self, asset_id: str) -> str:
        return self.aliases.get(asset_id, asset_id)

    def get_asset(self, asset_id: str) -> VisualAssetPrompt | None:
        return self.assets.get(self.normalize_asset_id(asset_id))

    def build_generated_script_prompt(
        self,
        *,
        asset_title: str,
        asset_type: str,
        dynasty_name: str,
        style_keywords: list[str],
        required_subjects: list[str],
        era_feature_checklist: list[str],
    ) -> str:
        return (
            f"{dynasty_name}历史悬疑游戏视觉资产，类型：{asset_type}，主题：{asset_title}。\n"
            f"画面必须清楚呈现：{'、'.join(required_subjects)}。\n"
            f"时代特征检查：{'、'.join(era_feature_checklist)}。\n"
            f"整体风格：{'、'.join(style_keywords)}。无现代物件、无文字水印、无占位构图。"
        )


    def list_assets(self) -> list[VisualAssetPrompt]:
        return list(self.assets.values())

    def p0_asset_ids(self) -> list[str]:
        return [asset.asset_id for asset in self.list_assets()]

    def _compose(self, subject: str) -> str:
        return f"{subject}, {UNIFIED_STYLE_PROMPT}"

    def _compose_clue(self, subject: str) -> str:
        return self._compose(f"{subject}, {CLUE_PROMPT_SUFFIX}")

    def _data_dir(self) -> Path:
        return Path(__file__).resolve().parents[2] / "data"

    def _load_json(self, relative_path: str) -> dict:
        path = self._data_dir() / relative_path
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _asset_id_from_path(self, value: str, fallback: str) -> str:
        if not value:
            return fallback
        return Path(value).stem or fallback

    def _scene_title(self, scene: dict) -> str:
        scene_id = str(scene.get("scene_id", ""))
        return SCENE_TITLES.get(scene_id, str(scene.get("name") or scene_id))

    def _npc_title(self, npc: dict) -> str:
        npc_id = str(npc.get("npc_id", ""))
        return NPC_TITLES.get(npc_id, str(npc.get("name") or npc_id))

    def _npc_scene_line(self, npc: dict) -> str:
        npc_id = str(npc.get("npc_id", ""))
        fallback = (
            f"{self._npc_title(npc)}，身份为{npc.get('public_identity') or '明代案件人物'}，"
            f"外貌：{npc.get('appearance') or '明代市井人物'}。"
        )
        base = NPC_SCENE_DESCRIPTIONS.get(npc_id, fallback)
        character_lock = CHARACTER_STYLE_LOCKS.get(npc_id)
        return f"{base} {character_lock}" if character_lock else base

    def _hotspot_visual_line(self, hotspot: dict) -> str:
        hotspot_id = str(hotspot.get("hotspot_id", ""))
        fallback = hotspot.get("description") or hotspot.get("label") or hotspot_id
        return HOTSPOT_VISUAL_HINTS.get(hotspot_id, str(fallback))

    def _clue_visual_line(self, clue: dict) -> str:
        clue_id = str(clue.get("clue_id", ""))
        fallback = f"{clue.get('title') or clue_id}：{clue.get('display_text') or clue.get('detail') or '可调查物证'}"
        return CLUE_VISUAL_HINTS.get(clue_id, fallback)

    def _scene_prompt_subject(self, scene: dict, scene_clues: list[dict], scene_npcs: list[dict]) -> str:
        scene_id = str(scene.get("scene_id", ""))
        scene_title = self._scene_title(scene)
        blueprint = SCENE_BLUEPRINTS.get(scene_id, f"{scene_title}：{scene.get('description') or scene.get('scene_text')}")
        npc_lines = [self._npc_scene_line(npc) for npc in scene_npcs]
        clue_lines = [self._clue_visual_line(clue) for clue in scene_clues]
        hotspot_lines = [self._hotspot_visual_line(hotspot) for hotspot in scene.get("hotspots", [])]

        return (
            f"生成一张网页游戏主场景图：明代应天府雨夜，书坊焚稿案，当前地点是{scene_title}。"
            f"{blueprint}"
            f"人物要求：{'; '.join(npc_lines) if npc_lines else '本场景无主要 NPC，画面重点放在可调查地点和物证上。'}"
            "人物必须和地点一起生成，处在同一透视、同一光源、同一色温里，不能像后期贴上去的半身立绘。"
            f"线索地点要素必须在画面中清晰可辨、方便玩家点击：{'; '.join(hotspot_lines) if hotspot_lines else '书坊内的可疑物件'}。"
            f"关键线索物件：{'; '.join(clue_lines) if clue_lines else '本场景暂无线索物件'}。"
            "构图要求：人物不要挡住关键线索，线索物件不要堆在画面边缘；前景、中景、背景层次明确；"
            "柜台、书柜、架子、旧书箱、门闩、告示、封条等物件要与场景位置关系合理。"
            "文书、告示、封条只表现纸张、印痕、折角、烧痕和圈点形态，不出现可读文字或乱码。"
            "整体低饱和国风悬疑，雨夜冷光与焚火暖光交错，暗金和克制朱红点缀。"
        )

    def _npc_prompt_subject(self, npc: dict) -> str:
        npc_id = str(npc.get("npc_id", ""))
        character_lock = CHARACTER_STYLE_LOCKS.get(npc_id, "")
        return (
            f"明代书坊焚稿案人物半身立绘：{npc.get('name')}，身份为{npc.get('public_identity')}。"
            f"外貌：{npc.get('appearance')}。性格：{npc.get('personality')}。"
            f"案件状态：{npc.get('event_behavior')}。"
            f"{character_lock} "
            "低饱和国风悬疑视觉小说人物，雨夜冷光与书坊烛火暖光混合，"
            "衣物、发式和姿态符合明代市井人物，不要现代服装，不要夸张卡通，"
            "边缘柔和，便于与雨夜书坊背景融合"
        )

    def _clue_prompt_subject(self, clue: dict, scene_name: str) -> str:
        return (
            f"{clue.get('title')}：{clue.get('display_text')}。"
            f"所属朝代为明代，所属场景为{scene_name or '明代书坊案现场'}。"
            f"线索细节：{clue.get('detail')}。"
            "材质与状态必须具体可见，带有雨夜潮湿、烛火微光、纸灰或木质书坊环境反光，"
            "与书坊焚稿案有明确视觉关联，暗金低饱和历史悬疑风格"
        )

    def _data_driven_assets(self, scene_size: str, npc_size: str, clue_size: str) -> list[VisualAssetPrompt]:
        scenes = self._load_json("scenes/ming_bookshop_scenes.json").get("scenes", [])
        npcs = self._load_json("npcs/ming_bookshop_npcs.json").get("npcs", [])
        clues = self._load_json("clues/ming_bookshop_clues.json").get("clues", [])
        clue_map = {clue.get("clue_id"): clue for clue in clues}
        npc_map = {npc.get("npc_id"): npc for npc in npcs}
        scene_name_by_id = {scene.get("scene_id"): scene.get("name", "") for scene in scenes}
        items: list[VisualAssetPrompt] = []

        for scene in scenes:
            scene_clue_ids: list[str] = []
            for hotspot in scene.get("hotspots", []):
                for clue_id in hotspot.get("clue_ids", []):
                    if clue_id not in scene_clue_ids:
                        scene_clue_ids.append(clue_id)
            scene_clues = [clue_map[clue_id] for clue_id in scene_clue_ids if clue_id in clue_map]
            scene_npcs = [npc_map[npc_id] for npc_id in scene.get("npc_ids", []) if npc_id in npc_map]
            asset_id = self._asset_id_from_path(scene.get("background_asset", ""), str(scene.get("scene_id", "")))
            items.append(
                VisualAssetPrompt(
                    asset_id=asset_id,
                    category="scenes",
                    title=self._scene_title(scene),
                    image_size=scene_size,
                    prompt=self._compose(self._scene_prompt_subject(scene, scene_clues, scene_npcs)),
                )
            )

        npc_asset_ids = {
            "npc_owner": "npc_xu_owner",
            "npc_worker": "npc_ashen_worker",
            "npc_scholar": "npc_guwen_scholar",
            "npc_jinyiwei": "npc_luzheng_jinyiwei",
        }
        for npc in npcs:
            asset_id = npc_asset_ids.get(npc.get("npc_id"), str(npc.get("npc_id", "")))
            items.append(
                VisualAssetPrompt(
                    asset_id=asset_id,
                    category="npcs",
                    title=self._npc_title(npc),
                    image_size=npc_size,
                    prompt=self._compose(self._npc_prompt_subject(npc)),
                )
            )

        for clue in clues:
            scene_name = scene_name_by_id.get(clue.get("source_scene_id"), "")
            items.append(
                VisualAssetPrompt(
                    asset_id=str(clue.get("clue_id")),
                    category="clues",
                    title=str(clue.get("title", clue.get("clue_id"))),
                    image_size=clue_size,
                    prompt=self._compose_clue(self._clue_prompt_subject(clue, scene_name)),
                )
            )

        return [item for item in items if item.asset_id]

    def _build_assets(self) -> dict[str, VisualAssetPrompt]:
        scene_size = "1024x1024"
        npc_size = "768x1024"
        clue_size = "1024x1024"
        items = [
            VisualAssetPrompt(
                asset_id="scene_bookshop_front_hall",
                category="scenes",
                title="书坊前厅",
                image_size=scene_size,
                prompt=self._compose("Ming dynasty bookshop front hall at rainy night, dim oil lamps suppressed by rain, wooden counter, account books, old book crates, drifting paper ash, no people in foreground"),
            ),
            VisualAssetPrompt(
                asset_id="scene_bookshop_backyard_fire",
                category="scenes",
                title="书坊后院火场",
                image_size=scene_size,
                prompt=self._compose("Ming dynasty bookshop backyard fire scene after rain, fire glow, smoke, scorched wooden shelves, scattered paper fragments, wet stone floor, oppressive mystery mood"),
            ),
            VisualAssetPrompt(
                asset_id="scene_account_room",
                category="scenes",
                title="账房暗格",
                image_size=scene_size,
                prompt=self._compose("small cramped Ming dynasty bookshop account room, ledgers on a narrow desk, hidden drawer half-open, fresh wood shavings near lock, small pile of paper ash in the corner, dim oil lamp, suspenseful investigation background"),
            ),
            VisualAssetPrompt(
                asset_id="scene_lamp_shelf",
                category="scenes",
                title="灯油架旁",
                image_size=scene_size,
                prompt=self._compose("Ming dynasty bookshop lamp oil shelf after rain, tipped oil jars, suspicious oil stains near wall root, rainwater footprints on wet floor, dragged lamp stand marks, dark fire investigation atmosphere"),
            ),
            VisualAssetPrompt(
                asset_id="scene_burned_printing_room",
                category="scenes",
                title="烧毁的刻版间",
                image_size=scene_size,
                prompt=self._compose("burned Ming dynasty printing and woodblock carving room, charred wooden boards, broken engraved blocks, oil stain traces, dark interior, ink residue, suspenseful investigation background"),
            ),
            VisualAssetPrompt(
                asset_id="scene_back_gate",
                category="scenes",
                title="后门雨泥处",
                image_size=scene_size,
                prompt=self._compose("back gate of a Ming dynasty bookshop in rain and mud, wet footprints leaving and returning, scratched wooden latch, wall root with a tiny paper binding thread, narrow old doorway, tense night investigation mood"),
            ),
            VisualAssetPrompt(
                asset_id="scene_rain_alley",
                category="scenes",
                title="明代雨巷",
                image_size=scene_size,
                prompt=self._compose("Ming dynasty rain alley, bluestone road, umbrella silhouettes, distant night watch lanterns, wet walls, suppressed historical suspense atmosphere"),
            ),
            VisualAssetPrompt(
                asset_id="scene_city_gate",
                category="scenes",
                title="城门搜检口",
                image_size=scene_size,
                prompt=self._compose("Ming dynasty city gate search checkpoint at rainy night, guards with torches, blank sealed notice sheets on wall, paper bundles and book crates being inspected, tense historical suspense background"),
            ),
            VisualAssetPrompt(
                asset_id="scene_jinyiwei_interrogation",
                category="scenes",
                title="锦衣卫临时问话处",
                image_size=scene_size,
                prompt=self._compose("temporary Jinyiwei interrogation room in Ming dynasty, low candlelight, deep shadows, wooden table, paper seals, official documents, oppressive but historically grounded"),
            ),
            VisualAssetPrompt(
                asset_id="npc_xu_owner",
                category="npcs",
                title="许掌柜",
                image_size=npc_size,
                prompt=self._compose("half-body portrait silhouette of a middle-aged Ming dynasty bookshop owner, tired cautious face, plain scholar-merchant robe, hiding a secret, low detail visual novel character art, transparent-feeling dark background"),
            ),
            VisualAssetPrompt(
                asset_id="npc_ashen_worker",
                category="npcs",
                title="阿沈",
                image_size=npc_size,
                prompt=self._compose("half-body portrait silhouette of a young Ming dynasty woodblock engraver, ink on sleeves, nervous silent expression, simple worker clothes, visual novel NPC art, dark muted background"),
            ),
            VisualAssetPrompt(
                asset_id="npc_guwen_scholar",
                category="npcs",
                title="顾闻",
                image_size=npc_size,
                prompt=self._compose("half-body portrait silhouette of a thin failed Ming dynasty scholar, stubborn anxious eyes, worn old robe, holding damp manuscript edge, historical suspense visual novel character"),
            ),
            VisualAssetPrompt(
                asset_id="npc_luzheng_jinyiwei",
                category="npcs",
                title="陆峥",
                image_size=npc_size,
                prompt=self._compose("half-body portrait silhouette of a low-ranking Ming dynasty Jinyiwei officer, cold restrained posture, not a grand commander, dark official uniform appropriate to Ming dynasty, stern visual novel character"),
            ),
            VisualAssetPrompt(
                asset_id="npc_xu_owner_cutout",
                category="npcs",
                title="许掌柜透明立绘",
                image_size=npc_size,
                prompt=self._compose("transparent alpha cutout asset of Xu the Ming dynasty bookshop owner, half body, no background, no scenery, suitable for compositing into a rainy bookshop scene"),
            ),
            VisualAssetPrompt(
                asset_id="npc_ashen_worker_cutout",
                category="npcs",
                title="阿沈透明立绘",
                image_size=npc_size,
                prompt=self._compose("transparent alpha cutout asset of A Shen the Ming dynasty woodblock engraver, half body, no background, no scenery, suitable for compositing into a rainy bookshop scene"),
            ),
            VisualAssetPrompt(
                asset_id="npc_guwen_scholar_cutout",
                category="npcs",
                title="顾闻透明立绘",
                image_size=npc_size,
                prompt=self._compose("transparent alpha cutout asset of Gu Wen the failed Ming dynasty scholar holding damp manuscript, half body, no background, no scenery, suitable for compositing into a rainy alley scene"),
            ),
            VisualAssetPrompt(
                asset_id="npc_luzheng_jinyiwei_cutout",
                category="npcs",
                title="陆峥透明立绘",
                image_size=npc_size,
                prompt=self._compose("transparent alpha cutout asset of Lu Zheng the low-ranking Ming dynasty Jinyiwei officer, half body, no background, no scenery, suitable for compositing into an interrogation scene"),
            ),
            VisualAssetPrompt(
                asset_id="clue_burned_page",
                category="clues",
                title="烧焦残页",
                image_size=clue_size,
                prompt=self._compose_clue("close-up clue illustration of a charred blank manuscript fragment in wet ash, torn burned edges, red ember glow, Ming dynasty paper texture, the clue is shown by burn pattern and paper state only"),
            ),
            VisualAssetPrompt(
                asset_id="clue_red_seal_fragment",
                category="clues",
                title="半枚红印纸角",
                image_size=clue_size,
                prompt=self._compose_clue("close-up clue illustration of half red-seal paper corner caught in an old book crate, blank damp official paper texture, torn edge, dark investigation lighting"),
            ),
            VisualAssetPrompt(
                asset_id="clue_missing_manuscript_list",
                category="clues",
                title="缺口整齐的稿单",
                image_size=clue_size,
                prompt=self._compose_clue("close-up clue illustration of blank manuscript account paper with a neatly cut missing corner, Ming dynasty bookshop paper texture, candle shadow, no writing on the sheet"),
            ),
            VisualAssetPrompt(
                asset_id="clue_oil_smell",
                category="clues",
                title="异常火油痕",
                image_size=clue_size,
                prompt=self._compose_clue("close-up clue illustration of abnormal fire oil stains on wet stone near a lamp shelf, dark amber reflection, Ming dynasty bookshop fire investigation"),
            ),
            VisualAssetPrompt(
                asset_id="clue_jinyiwei_gag_order",
                category="clues",
                title="锦衣卫封口令",
                image_size=clue_size,
                prompt=self._compose_clue("close-up clue illustration of a folded blank Ming dynasty official order document under a red seal, damp paper, candlelight, oppressive official atmosphere, the seal and folds carry the clue without any written words"),
            ),
        ]
        items.extend(self._data_driven_assets(scene_size=scene_size, npc_size=npc_size, clue_size=clue_size))
        return {item.asset_id: item for item in items}


visual_prompt_agent = VisualPromptAgent()

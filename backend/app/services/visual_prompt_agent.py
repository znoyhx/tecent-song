from __future__ import annotations

from dataclasses import dataclass


UNIFIED_STYLE_PROMPT = (
    "low-saturation Chinese historical suspense visual novel style, "
    "Ming dynasty bookshop mystery, dark cinematic lighting, rain night, "
    "fire glow, smoke, paper ash, muted ink wash texture mixed with digital painting, "
    "no modern objects, no modern clothes, no neon, no western fantasy, no guns, "
    "no cars, no electricity, no anachronistic architecture, serious atmosphere, "
    "game background art, high detail, moody composition"
)

NEGATIVE_PROMPT = (
    "modern city, modern clothes, electric light, neon, car, gun, phone, "
    "western fantasy armor, anime school uniform, sci-fi, futuristic, bright cartoon, "
    "cute style, comedy, low quality, blurry, distorted, wrong dynasty, "
    "Qing dynasty queue hairstyle, Qing eight banners, Japanese samurai, modern police, "
    "Republican era clothes, English signs, gore, sexual content"
)



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
            "clue_red_seal": "clue_red_seal_fragment",
        }

    def normalize_asset_id(self, asset_id: str) -> str:
        return self.aliases.get(asset_id, asset_id)

    def get_asset(self, asset_id: str) -> VisualAssetPrompt | None:
        return self.assets.get(self.normalize_asset_id(asset_id))


    def list_assets(self) -> list[VisualAssetPrompt]:
        return list(self.assets.values())

    def p0_asset_ids(self) -> list[str]:
        return [
            "scene_bookshop_front_hall",
            "scene_bookshop_backyard_fire",
            "scene_account_room",
            "scene_lamp_shelf",
            "scene_burned_printing_room",
            "scene_back_gate",
            "scene_rain_alley",
            "scene_city_gate",
            "scene_jinyiwei_interrogation",
            "npc_xu_owner",
            "npc_ashen_worker",
            "npc_guwen_scholar",
            "npc_luzheng_jinyiwei",
        ]

    def _compose(self, subject: str) -> str:
        return f"{subject}, {UNIFIED_STYLE_PROMPT}"

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
                prompt=self._compose("Ming dynasty city gate search checkpoint at rainy night, guards with torches, wet official search notice on wall, paper bundles and book crates being inspected, tense historical suspense background"),
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
                asset_id="clue_burned_page",
                category="clues",
                title="烧焦残页",
                image_size=clue_size,
                prompt=self._compose("close-up clue illustration of a burned manuscript fragment in wet ash, faint Chinese characters suggesting Liaodong grain register, red ember glow, Ming dynasty paper texture"),
            ),
            VisualAssetPrompt(
                asset_id="clue_red_seal_fragment",
                category="clues",
                title="半枚红印纸角",
                image_size=clue_size,
                prompt=self._compose("close-up clue illustration of half red seal paper corner caught in an old book crate, Ming dynasty official document texture, wet paper, dark investigation lighting"),
            ),
            VisualAssetPrompt(
                asset_id="clue_missing_manuscript_list",
                category="clues",
                title="缺口整齐的稿单",
                image_size=clue_size,
                prompt=self._compose("close-up clue illustration of a manuscript list with a neatly cut missing corner, ink brush writing, Ming dynasty bookshop account paper, candle shadow"),
            ),
            VisualAssetPrompt(
                asset_id="clue_oil_smell",
                category="clues",
                title="异常火油痕",
                image_size=clue_size,
                prompt=self._compose("close-up clue illustration of abnormal fire oil stains on wet stone near a lamp shelf, dark amber reflection, Ming dynasty bookshop fire investigation"),
            ),
            VisualAssetPrompt(
                asset_id="clue_jinyiwei_gag_order",
                category="clues",
                title="锦衣卫封口令",
                image_size=clue_size,
                prompt=self._compose("close-up clue illustration of a Ming dynasty Jinyiwei gag order document under a red seal, damp paper, candlelight, oppressive official atmosphere"),
            ),
        ]
        return {item.asset_id: item for item in items}


visual_prompt_agent = VisualPromptAgent()

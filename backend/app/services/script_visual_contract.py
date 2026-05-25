from __future__ import annotations

from copy import deepcopy
import hashlib

from app.models.script_models import ImageQualityGateResult, ScriptPackage, VisualAsset


VISUAL_CONTRACT_VERSION = "script_visual_contract_v2"
SCENE_NPC_CONTRACT = "scene_requires_visible_npcs"
SCENE_CLUE_CONTRACT = "scene_requires_visible_clue_objects"
CLUE_CLOSEUP_CONTRACT = "clue_object_closeup_no_readable_text"
NPC_PORTRAIT_CONTRACT = "npc_portrait_identity_lock"
SCENE_NPC_MARKER = "scene_npc:"
SCENE_CLUE_MARKER = "scene_clue:"
CLUE_OWNER_MARKER = "clue_owner:"
NPC_IDENTITY_MARKER = "npc_identity:"


class ScriptVisualContract:
    def apply(self, package: ScriptPackage, *, reset_assets: bool = False) -> ScriptPackage:
        updated = deepcopy(package)
        locations = {location.location_id: location for location in updated.locations}
        npcs = {npc.npc_id: npc for npc in updated.npcs}
        clues = {clue.clue_id: clue for clue in updated.clues}

        for asset in updated.visual_assets:
            if asset.asset_type == "scene":
                location = locations.get(asset.owner_id) or next(
                    (item for item in updated.locations if item.visual_asset_id == asset.asset_id),
                    None,
                )
                if location is not None:
                    scene_npcs = [npcs[npc_id] for npc_id in location.npc_ids if npc_id in npcs]
                    scene_clue_ids = [
                        clue_id
                        for hotspot in location.hotspots
                        for clue_id in hotspot.clue_ids
                        if clue_id in clues
                    ]
                    scene_clues = [clues[clue_id] for clue_id in dict.fromkeys(scene_clue_ids).keys()]
                    asset.prompt = self._scene_prompt(updated, location, scene_npcs, scene_clues)
                    asset.negative_prompt = self._append_unique(
                        asset.negative_prompt,
                        [
                            "empty street without people",
                            "empty room without people",
                            "no visible NPC",
                            "tiny distant people only",
                            "landscape-only",
                            "architecture-only",
                            "animal-only",
                            "object-only",
                            "missing clue object",
                            "modern object",
                            "watermark",
                            "readable generated text",
                            "wrong dynasty costume",
                        ],
                    )
                    asset.required_subjects = self._merge_subjects(
                        asset.required_subjects,
                        [
                            *[npc.name for npc in scene_npcs],
                            *[self._scene_npc_marker(npc) for npc in scene_npcs],
                            *[clue.title for clue in scene_clues[:6]],
                            *[self._scene_clue_marker(clue) for clue in scene_clues[:6]],
                            SCENE_NPC_CONTRACT,
                            SCENE_CLUE_CONTRACT,
                            VISUAL_CONTRACT_VERSION,
                        ],
                    )
            elif asset.asset_type == "npc":
                npc = npcs.get(asset.owner_id) or next(
                    (item for item in updated.npcs if item.visual_asset_id == asset.asset_id),
                    None,
                )
                if npc is not None:
                    asset.prompt = self._npc_prompt(updated, npc)
                    asset.negative_prompt = self._append_unique(
                        asset.negative_prompt,
                        [
                            "modern clothing",
                            "modern object",
                            "watermark",
                            "readable generated text",
                            "empty background only",
                            "wrong dynasty costume",
                        ],
                    )
                    asset.required_subjects = self._merge_subjects(
                        asset.required_subjects,
                        [
                            npc.name,
                            npc.public_identity,
                            self._npc_identity_marker(npc),
                            NPC_PORTRAIT_CONTRACT,
                            VISUAL_CONTRACT_VERSION,
                        ],
                    )
            elif asset.asset_type == "clue":
                clue = clues.get(asset.owner_id) or next(
                    (item for item in updated.clues if item.visual_asset_id == asset.asset_id),
                    None,
                )
                if clue is not None:
                    asset.prompt = self._clue_prompt(updated, clue)
                    asset.negative_prompt = self._append_unique(
                        asset.negative_prompt,
                        [
                            "wide street scene",
                            "crowd scene",
                            "portrait",
                            "readable text",
                            "Chinese characters",
                            "calligraphy",
                            "legible writing",
                            "character-like marks",
                            "symbols",
                            "open document text",
                            "garbled text",
                            "watermark",
                            "modern object",
                        ],
                    )
                    asset.required_subjects = self._merge_subjects(
                        asset.required_subjects,
                        [
                            clue.title,
                            self._clue_owner_marker(clue),
                            "evidence close-up",
                            "material detail",
                            CLUE_CLOSEUP_CONTRACT,
                            VISUAL_CONTRACT_VERSION,
                        ],
                    )

            next_hash = self.prompt_hash(asset)
            if reset_assets or asset.prompt_hash != next_hash:
                asset.generated_path = None
                asset.url = None
                asset.provider = None
                asset.model = None
                asset.generation_status = "pending"
                asset.quality_gate = ImageQualityGateResult(status="pending", issues=[], prompt_hash=next_hash)
            asset.prompt_hash = next_hash

        return updated

    def prompt_hash(self, asset: VisualAsset) -> str:
        return hashlib.sha256(asset.prompt.encode("utf-8")).hexdigest()[:16]

    def _scene_prompt(self, package: ScriptPackage, location, scene_npcs, scene_clues) -> str:
        dynasty_name = package.world.dynasty_name if package.world else package.dynasty_id
        style_keywords = ", ".join(package.visual_style_guide.style_keywords[:8])
        npc_text = "; ".join(
            f"{npc.name} ({npc.public_identity}; appearance lock: "
            f"{package.visual_style_guide.appearance_lock.get(npc.npc_id) or npc.appearance})"
            for npc in scene_npcs
        ) or "at least one historically grounded case NPC"
        clue_text = "; ".join(clue.title for clue in scene_clues[:6]) or "clickable evidence objects tied to the case"
        marker_text = "; ".join(
            [
                *[self._scene_npc_marker(npc) for npc in scene_npcs],
                *[self._scene_clue_marker(clue) for clue in scene_clues[:6]],
            ]
        )
        return (
            f"{dynasty_name} historical mystery game main scene, integrated environment illustration, "
            "not an empty street and not a pure background. PRIMARY SUBJECT: one large visible adult human NPC in historical Song clothing is mandatory; "
            "the location is the background, not the main subject. Compose the person at left or center foreground. "
            f"Location: {location.name}. Environment: {location.description}. "
            f"At least one named NPC from this list must be foreground-visible, full-body or waist-up, face and hands visible, "
            f"occupying 30-45 percent of the frame, in the same perspective and light: {npc_text}. "
            "Additional NPCs may stand nearby, but people must not be tiny distant silhouettes. "
            f"Clickable evidence objects must be clear and locatable in the scene: {clue_text}. "
            "Never output an empty room, empty street, empty courtyard, object-only room, landscape-only view, architecture-only view, or horse-only scene; "
            "every scene needs a visible named human suspect or witness. "
            "NPCs, buildings, furniture, and evidence share one coherent historical light source and dynasty costume system. "
            "Use a grounded investigation camera, readable silhouettes, no modern objects, no watermark, no generated readable text. "
            f"Style: {style_keywords}. "
            f"Contract: {SCENE_NPC_CONTRACT}; {SCENE_CLUE_CONTRACT}; {VISUAL_CONTRACT_VERSION}. "
            f"QA markers: {marker_text}."
        )

    def _npc_prompt(self, package: ScriptPackage, npc) -> str:
        dynasty_name = package.world.dynasty_name if package.world else package.dynasty_id
        appearance = package.visual_style_guide.appearance_lock.get(npc.npc_id) or npc.appearance
        style_keywords = ", ".join(package.visual_style_guide.style_keywords[:8])
        return (
            f"{dynasty_name} historical mystery NPC portrait for {npc.name}, public identity: {npc.public_identity}. "
            f"Appearance lock: {appearance}. Personality: {npc.personality}. "
            "Show the person clearly as a usable character portrait, historically grounded clothing, "
            "no modern object, no watermark, no readable text. "
            f"Style: {style_keywords}. "
            f"Contract: {NPC_PORTRAIT_CONTRACT}; {VISUAL_CONTRACT_VERSION}; {self._npc_identity_marker(npc)}."
        )

    def _clue_prompt(self, package: ScriptPackage, clue) -> str:
        dynasty_name = package.world.dynasty_name if package.world else package.dynasty_id
        return (
            f"{dynasty_name} historical mystery evidence close-up, one core object fills the frame: {clue.title}. "
            f"Evidence note: {clue.display_text}. "
            "Zero visible writing marks or symbols. For any paper, ledger, register, note, or document clue, show only a closed cover, folded blank edge, cord, seal, wax, burn, tear, stain, or smudged blank surface. "
            "Show material detail only: fold marks, damaged edge, blood trace, mud trace, burn mark, seal, fiber, "
            "or broken surface as appropriate. "
            "If the clue is a document, draw the folded, rolled, sealed, torn, or burned exterior and material surface only; "
            "do not show an open page, columns, character-like strokes, symbols, or any marks that resemble text. "
            "Do not draw a street scene, crowd, portrait, large environment, readable body text, garbled text, "
            "Chinese characters, calligraphy, symbols, watermark, or modern object. "
            "The object must be clear, near-camera, useful as a clue-card thumbnail. "
            f"Contract: {CLUE_CLOSEUP_CONTRACT}; {VISUAL_CONTRACT_VERSION}; {self._clue_owner_marker(clue)}."
        )

    def _scene_npc_marker(self, npc) -> str:
        return f"{SCENE_NPC_MARKER}{npc.npc_id}:{npc.name}"

    def _scene_clue_marker(self, clue) -> str:
        return f"{SCENE_CLUE_MARKER}{clue.clue_id}:{clue.title}"

    def _clue_owner_marker(self, clue) -> str:
        return f"{CLUE_OWNER_MARKER}{clue.clue_id}:{clue.title}"

    def _npc_identity_marker(self, npc) -> str:
        return f"{NPC_IDENTITY_MARKER}{npc.npc_id}:{npc.name}"

    def _merge_subjects(self, current: list[str], additions: list[str]) -> list[str]:
        return list(dict.fromkeys([item for item in [*current, *additions] if item]))

    def _append_unique(self, current: str, additions: list[str]) -> str:
        normalized = current.replace(";", ",")
        pieces = [piece.strip() for piece in normalized.split(",") if piece.strip()]
        pieces.extend(additions)
        return ", ".join(dict.fromkeys(pieces))


script_visual_contract = ScriptVisualContract()

from __future__ import annotations

from copy import deepcopy
import hashlib

from app.models.script_models import ImageQualityGateResult, ScriptPackage, VisualAsset
from app.services.hotspot_layout_contract import HOTSPOT_LAYOUT_VERSION, prompt_line
from app.services.visual_clue_sanitizer import concrete_clue_visual_subject, scene_clue_visual_requirement


VISUAL_CONTRACT_VERSION = "script_visual_contract_v4"
SCENE_NPC_CONTRACT = "scene_requires_visible_npcs"
SCENE_CLUE_CONTRACT = "scene_requires_visible_clue_objects"
SCENE_COMPOSITION_CONTRACT = "scene_requires_centered_full_face_upper_body"
SCENE_CENTERED_CLUE_CONTRACT = "scene_requires_centered_clue_objects"
SCENE_SLOT_LAYOUT_CONTRACT = "scene_requires_declared_safe_hotspot_slots"
SCENE_LOCATION_CONTEXT_CONTRACT = "scene_uses_location_story_context"
SCENE_CLUE_DETAIL_CONTRACT = "scene_requires_clue_detail_placement"
SCENE_STYLE_GUIDE_CONTRACT = "scene_style_follows_script_visual_guide"
UNIFIED_STYLE_CONTRACT = "visual_style_unified_across_scene_npc_clue"
VISUAL_SELF_CHECK_CONTRACT = "post_generation_visual_self_check_required"
CLUE_CLOSEUP_CONTRACT = "clue_object_closeup_no_readable_text"
CLUE_CONCRETE_OBJECT_CONTRACT = "clue_requires_concrete_object_not_abstract_diagram"
NPC_PORTRAIT_CONTRACT = "npc_portrait_identity_lock"
SCENE_NPC_MARKER = "scene_npc:"
SCENE_CLUE_MARKER = "scene_clue:"
SCENE_CLUE_DETAIL_MARKER = "scene_clue_detail:"
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
                            "cropped head",
                            "cropped face",
                            "back-facing main character",
                            "rear view",
                            "from behind",
                            "main character turned away",
                            "face hidden",
                            "looking away",
                            "profile-only face",
                            "side profile",
                            "profile view",
                            "extra people",
                            "background person",
                            "second person",
                            "extreme close-up portrait",
                            "large crowd",
                            "army formation",
                            "troop formation",
                            "massed soldiers",
                            "soldier rows",
                            "guard corridor",
                            "cavalry scene",
                            "battle scene",
                            "flags",
                            "weapons",
                            "landscape-only",
                            "architecture-only",
                            "animal-only",
                            "object-only",
                            "missing clue object",
                            "clue object at edge",
                            "signboard",
                            "plaque",
                            "banner",
                            "gate sign",
                            "entrance sign",
                            "sign above gate",
                            "calligraphy",
                            "Chinese characters",
                            "text-like marks",
                            "abstract timeline",
                            "timeline diagram",
                            "laboratory glassware",
                            "conical flask",
                            "Erlenmeyer flask",
                            "beaker",
                            "test tube",
                            "modern glass bottle",
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
                            *[self._scene_clue_detail_marker(clue) for clue in scene_clues[:6]],
                            SCENE_NPC_CONTRACT,
                            SCENE_CLUE_CONTRACT,
                            SCENE_COMPOSITION_CONTRACT,
                            SCENE_CENTERED_CLUE_CONTRACT,
                            SCENE_SLOT_LAYOUT_CONTRACT,
                            SCENE_LOCATION_CONTEXT_CONTRACT,
                            SCENE_CLUE_DETAIL_CONTRACT,
                            SCENE_STYLE_GUIDE_CONTRACT,
                            HOTSPOT_LAYOUT_VERSION,
                            UNIFIED_STYLE_CONTRACT,
                            VISUAL_SELF_CHECK_CONTRACT,
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
                            "anime",
                            "cartoon",
                            "chibi",
                            "cropped head",
                            "cropped face",
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
                            "timeline",
                            "timeline diagram",
                            "abstract diagram",
                            "relationship graph",
                            "flow chart",
                            "concept map",
                            "laboratory glassware",
                            "conical flask",
                            "Erlenmeyer flask",
                            "beaker",
                            "test tube",
                            "modern glass bottle",
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
                            CLUE_CONCRETE_OBJECT_CONTRACT,
                            UNIFIED_STYLE_CONTRACT,
                            VISUAL_SELF_CHECK_CONTRACT,
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
        era_rules = self._era_prop_rules(package.dynasty_id)
        primary_npcs = scene_npcs[:2]
        npc_text = "; ".join(
            f"{npc.name} (appearance lock: "
            f"{package.visual_style_guide.appearance_lock.get(npc.npc_id) or npc.appearance})"
            for npc in primary_npcs
        ) or "at least one historically grounded case NPC"
        clue_subjects = [
            concrete_clue_visual_subject(clue.title, index=index, location_name=location.name)
            for index, clue in enumerate(scene_clues[:6])
        ]
        clue_requirements = [
            scene_clue_visual_requirement(clue, index=index, location_name=location.name)
            for index, clue in enumerate(scene_clues[:6])
        ]
        clue_text = "; ".join(clue_subjects) or "clickable concrete evidence objects tied to the case"
        clue_requirement_text = " | ".join(clue_requirements) or "clickable concrete evidence objects tied to the case must be visible in the scene"
        slot_text = "; ".join(
            prompt_line(index, concrete_clue_visual_subject(clue.title, index=index, location_name=location.name), location.location_id)
            for index, clue in enumerate(scene_clues[:6])
        ) or "place concrete evidence in the declared safe center slots"
        location_context = (
            f"Location name: {location.name}. "
            f"Location description: {location.description}. "
            f"Scene text: {location.scene_text}. "
            f"Story surface event: {package.story.surface_event}. "
            f"Public objective: {package.script_overview.public_objective}."
        )
        marker_text = "; ".join(
            [
                *[self._scene_npc_marker(npc) for npc in scene_npcs],
                *[self._scene_clue_marker(clue) for clue in scene_clues[:6]],
                *[self._scene_clue_detail_marker(clue) for clue in scene_clues[:6]],
            ]
        )
        return (
            f"{dynasty_name} historical mystery game main scene, refined Chinese historical suspense illustration following this script's visual style guide, "
            "ink-wash texture mixed with refined digital painting, cinematic rain/fire/lamp atmosphere, elegant but ominous composition. "
            "wide 16:9 landscape composition for a game stage, not square, not vertical, not portrait format, no black side padding. "
            f"Use the actual story location instead of a generic courtyard: {location_context} "
            "Build the composition from that location: if it is a dock, show dock stones, water edge, mooring objects, cargo shadows; if it is a study or residence, show desk, shelf, hidden compartment, floor mats, lamp and wall structure; if it is a tea house, show tea tables, screens, upstairs railings, cups and rainy eaves; if it is a pawnshop, show counter, shelves, boxes, pawn tokens and account objects. "
            "Do not collapse every location into the same evidence table template. "
            "PRIMARY SUBJECT: one primary visible adult living NPC in historical clothing stands or sits naturally inside the location and shares the same light and perspective; "
            "full face and upper body should be readable, no cropped head, no cropped chin, no oversized torso crop, never rear view, never back-facing, never face-hidden. "
            "The main person should occupy about 18-30 percent of the frame width so the environment and clue objects remain visible. "
            "Living human count rule: one primary NPC is preferred; if the clue requires a corpse, the corpse must appear as evidence and does not count as an extra living NPC. "
            "Do not make a crowd scene, army formation, cavalry scene, battlefield, parade, line of troops, street procession, or guard corridor. "
            "Do not draw guard lines, troop formations, massed soldiers, horse teams, city-gate queues, ceremonial entrances, flags, banners, weapons, or military staging even if the story location mentions them. "
            f"Named NPC appearance lock for this scene: {npc_text}. "
            "No additional guards, servants, soldiers, clerks, rows, silhouettes, or crowds may appear anywhere. "
            f"Clickable evidence objects must be clear, visible, and close to the center third of the image: {clue_text}. "
            f"Hard scene clue requirements, all must be visible as image content and not merely named in labels: {clue_requirement_text}. "
            f"Top-priority evidence slot contract: place these props as physical objects at the matching normalized image positions and keep them recognizable: {slot_text}. "
            "Each evidence object must physically appear in the environment as a concrete prop, not as an abstract idea, not a label, not a timeline, not a diagram. "
            "Create several visible evidence zones in the middle third of the scene, using the natural location surfaces: table, counter, hidden compartment, floor, stone step, dock ground, body area, shelf, tray, or wall niche. "
            "Do not place evidence on sky, roof, high wall, signboard, plaque, or decorative text area. "
            "Keep important evidence away from image edges and away from UI-safe bottom space; leave enough empty air around each evidence object for hotspot markers. "
            "Never output an empty room, empty street, empty courtyard, object-only room, landscape-only view, architecture-only view, or horse-only scene; "
            "every scene needs a visible named human suspect or witness. "
            "NPCs, buildings, furniture, and evidence share one coherent historical light source and dynasty costume system. "
            f"Dynasty material audit: {era_rules}. "
            "Strictly forbid mountains, lakes, cabins, deer, western scenery, laboratory glassware, conical flasks, Erlenmeyer flasks, beakers, test tubes, modern glass bottles, plastic, electric lights, printed modern labels, modern furniture, and Western modern clothing. "
            "If the location contains a gate, shop, office, room entrance, inn entrance, archive, or hall, keep all lintels and panels blank; no signboard, no plaque, no banner, no readable characters above doors. "
            "Style must follow this script's own visual_style_guide: refined Chinese historical suspense illustration, painterly but readable, game-stage composition, coherent color script and camera, no ugly photorealistic plastic render, no bland stock courtyard, no random modern concept-art style. "
            "Use a grounded investigation camera and readable silhouettes. No modern objects, no watermark, no generated readable text, no Chinese characters, no calligraphy, no plaques, no banners, no signboards, no text-like decoration. "
            "Post-generation self-check: wide landscape ratio; location matches the named place; main NPC face and upper body visible but not oversized; every named clue requirement appears as a concrete object or trace at its declared slot; corpse clues show a corpse, empty-box clues show an open empty box, document clues show sealed/folded papers without readable text; dynasty props only; unified script-specific illustrated style; image successfully generated. "
            f"Style: {style_keywords}. "
            f"Contract: {SCENE_NPC_CONTRACT}; {SCENE_CLUE_CONTRACT}; {SCENE_COMPOSITION_CONTRACT}; "
            f"{SCENE_CENTERED_CLUE_CONTRACT}; {SCENE_SLOT_LAYOUT_CONTRACT}; {SCENE_LOCATION_CONTEXT_CONTRACT}; "
            f"{SCENE_CLUE_DETAIL_CONTRACT}; {SCENE_STYLE_GUIDE_CONTRACT}; {HOTSPOT_LAYOUT_VERSION}; "
            f"{UNIFIED_STYLE_CONTRACT}; {VISUAL_SELF_CHECK_CONTRACT}; {VISUAL_CONTRACT_VERSION}. "
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
            "front-facing or three-quarter view, face centered and complete, upper body complete, consistent with the main scene style, "
            "restrained realistic Chinese historical mystery illustration, no anime, no chibi, no modern object, no watermark, no readable text. "
            f"Style: {style_keywords}. "
            f"Contract: {NPC_PORTRAIT_CONTRACT}; {UNIFIED_STYLE_CONTRACT}; {VISUAL_SELF_CHECK_CONTRACT}; {VISUAL_CONTRACT_VERSION}; {self._npc_identity_marker(npc)}."
        )

    def _clue_prompt(self, package: ScriptPackage, clue) -> str:
        dynasty_name = package.world.dynasty_name if package.world else package.dynasty_id
        clue_subject = concrete_clue_visual_subject(clue.title)
        era_rules = self._era_prop_rules(package.dynasty_id)
        return (
            f"{dynasty_name} historical mystery evidence close-up, one concrete core object fills the frame: {clue_subject}. "
            f"Evidence note: {clue.display_text}. "
            "The clue image must show a tangible object, trace, document exterior, seal, residue, tool, fabric, footprint, rope, token, or damaged material. "
            "Never visualize abstract clues such as timeline, motive, relationship, suspicion, action chain, truth, contradiction, or evidence chain as charts or diagrams. "
            "Zero visible writing marks or symbols. For any paper, ledger, register, note, or document clue, show only a closed cover, folded blank edge, cord, seal, wax, burn, tear, stain, or smudged blank surface. "
            "Show material detail only: fold marks, damaged edge, blood trace, mud trace, burn mark, seal, fiber, "
            "or broken surface as appropriate. "
            "If the clue is a document, draw the folded, rolled, sealed, torn, or burned exterior and material surface only; "
            "do not show an open page, columns, character-like strokes, symbols, or any marks that resemble text. "
            "Do not draw a street scene, crowd, portrait, large environment, readable body text, garbled text, "
            "Chinese characters, calligraphy, symbols, timeline, diagram, relationship graph, flow chart, watermark, or modern object. "
            f"Dynasty material audit: {era_rules}. "
            "For liquid, medicine, poison, or wine clues, use ceramic cups, ceramic jars, lacquer boxes, gourds, paper packets, or cloth wraps only; never use conical flasks, Erlenmeyer flasks, beakers, test tubes, laboratory glassware, or modern bottles. "
            "The object must be clear, near-camera, useful as a clue-card thumbnail. "
            "Post-generation self-check: one concrete object only; no abstract chart; no readable text; unified style; image successfully generated. "
            f"Contract: {CLUE_CLOSEUP_CONTRACT}; {CLUE_CONCRETE_OBJECT_CONTRACT}; {UNIFIED_STYLE_CONTRACT}; {VISUAL_SELF_CHECK_CONTRACT}; {VISUAL_CONTRACT_VERSION}; {self._clue_owner_marker(clue)}."
        )

    def _era_prop_rules(self, dynasty_id: str) -> str:
        if dynasty_id == "song":
            return (
                "Northern Song props only: ceramic wine cups and jars, lacquered wood, bamboo, silk, hemp cloth, "
                "bronze or iron tools, paper documents shown closed or sealed, oil lamps, wooden furniture, tiled roofs, and period robes"
            )
        if dynasty_id == "late_tang":
            return (
                "Late Tang props only: ceramic vessels, bronze or iron tools, lacquered wood, silk, hemp cloth, "
                "paper documents shown closed or sealed, oil lamps, wooden furniture, and period robes"
            )
        return (
            "dynasty-appropriate Chinese historical props only: ceramic, lacquered wood, bamboo, silk, cloth, "
            "bronze or iron, paper documents shown closed or sealed, oil lamps, and period robes"
        )

    def _scene_npc_marker(self, npc) -> str:
        return f"{SCENE_NPC_MARKER}{npc.npc_id}:{npc.name}"

    def _scene_clue_marker(self, clue) -> str:
        return f"{SCENE_CLUE_MARKER}{clue.clue_id}:{clue.title}"

    def _scene_clue_detail_marker(self, clue) -> str:
        return f"{SCENE_CLUE_DETAIL_MARKER}{clue.clue_id}:{clue.title}"

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

# CODEBUDDY.md

This file provides guidance to CodeBuddy when working with code in this repository.

## Current Repository State

This repository is no longer documentation-only. It contains a working Stage 1 mock implementation of 《史隙》:

- `docs/PRD.md` defines the product, gameplay, AI/RAG/state-machine constraints, Phaser stage target, and the new DeepSeek AI script generation direction.
- `docs/develop/23_ai_script_generation_requirements.md` defines the Stage 15 generated-script requirements.
- `frontend/` contains a Vite + React + TypeScript demo frontend.
- `backend/` contains a FastAPI mock demo backend with game flow, clue rules, visual asset routes, dialogue orchestration, supervisor logic, and tests.
- `assets/` contains generated or prepared visual assets.

The current stable playable route is the Ming dynasty bookshop manuscript-burning case. Stage 15 changes the expansion plan: Ming remains the fixed roadshow demo and regression fallback, while Northern Song and Late Tang / late-period Tang enter a keyword-driven DeepSeek script-generation flow.

## Commands

Run commands from the repository root unless otherwise noted.

- `cd frontend; npm run dev` — start the Vite frontend.
- `cd frontend; npm run build` — type-check and build the frontend.
- `cd backend; python -m uvicorn app.main:app --reload` — start the FastAPI backend on the default development port.
- `cd backend; python -m pytest` — run backend tests.
- `rg <term>` or `rg --files` — preferred search commands for code and docs.

When Phaser is implemented, install it in `frontend/` with `npm install phaser` and confirm `frontend/package.json` before relying on the dependency.

## Product Direction

《史隙》 is an AI-driven historical suspense branching narrative web game, not a plain history chatbot or RAG Q&A system. The current stable demo remains:

```text
Ming dynasty / bookshop apprentice / bookshop manuscript-burning case
```

Stage 15 adds generated playable scripts for Northern Song and Late Tang:

```text
Choose Ming
  -> start the existing fixed bookshop manuscript-burning demo

Choose Northern Song or Late Tang
  -> fill 1-8 generation keywords
  -> DeepSeek generates and refines a ScriptPackage
  -> backend validates script logic, history, NPC permissions, visuals, and hotspot coordinates
  -> generated overview and generated identity selection
  -> start the generated script
```

The general user loop is:

```text
Choose dynasty and identity
  -> start a generated historical event world
  -> investigate the scene
  -> click highlighted clues
  -> collect clues in the side dossier
  -> question NPCs
  -> present evidence
  -> combine clues or submit deductions
  -> make an irreversible choice
  -> resolve into one of several endings
```

AI is responsible for world detail, NPC wording, emotional/action flavor, visual prompts, and history-echo prose. Code and rules must control clue release, stage transitions, score changes, NPC permissions, and ending eligibility.

For generated scripts, AI may draft the story world, NPCs, locations, clue graph, dialogue rules, choices, endings, visual prompts, visual style guide, appearance locks, and initial hotspot estimates. Backend schema validation, `ScriptSupervisor`, `ImageQualityGate`, `HotspotCalibrationService`, and the game engine remain authoritative. Do not let AI output directly mutate live game state.

## Frontend Architecture

Current important frontend files:

- `frontend/src/App.tsx` owns the main session state, API calls, selected NPC, action notice, and routing between start/generation/game/ending views.
- `frontend/src/pages/GamePage.tsx` lays out the game screen.
- `frontend/src/components/scene/ScenePanel.tsx` is the current React-only visual novel stage.
- `frontend/src/components/dialogue/DialoguePanel.tsx` owns long-form dialogue, suggested questions, free input, and evidence presentation.
- `frontend/src/components/clue/ClueSidebar.tsx` owns dossier, clues, locations, people, investigation actions, and deduction submission.
- `frontend/src/types/game.ts` defines the frontend contract for sessions, scenes, NPCs, clues, dialogue, choices, endings, and state.
- `frontend/src/api/client.ts` wraps the existing FastAPI endpoints.

Do not move the authoritative frontend session state out of `App.tsx` for the Phaser P0 work. A global store can be introduced later only if the UI complexity clearly requires it.

Stage 15 frontend work may add generated-script entry pages and components under `frontend/src/components/script-generation/*` or equivalent. These components must:

- keep Ming on the fixed demo route;
- show keyword input only for Northern Song and Late Tang;
- render generation progress from backend job `steps` only, with no fake timer-driven progress;
- allow historical quote rotation as atmosphere only, not as progress;
- show generated script overview from `script_overview`;
- show generated identity cards from `playable_identities`;
- call `POST /api/session/start-generated` with `script_id + identity_id`.

## Phaser Stage Target

The next frontend goal is:

> Upgrade the existing React visual novel stage into a React + Phaser hybrid narrative stage.

Phaser should enhance or replace only the `ScenePanel` layer. It must not become a second game system.

Recommended P0 files:

```text
frontend/src/components/scene/PhaserStage.tsx
frontend/src/game/phaserGame.ts
frontend/src/game/events.ts
frontend/src/game/scenes/MainScene.ts
frontend/src/game/objects/Hotspot.ts
frontend/src/game/objects/NPCSprite.ts
```

Keep `ScenePanel.tsx` in place as a fallback while introducing `PhaserStage.tsx`. Add a feature flag or local switch so the old React stage can be restored quickly if Phaser causes regressions.

### Phaser P0 Scope

Phaser should handle:

- scene background rendering from `snapshot.scene.visual_asset_url` or `snapshot.scene.visual_asset_id`;
- subtle NPC hit targets / focus feedback from `snapshot.scene_npcs`, assuming the NPC bodies are already baked into the scene image;
- selected NPC highlighting;
- clickable investigation hotspots from `snapshot.scene.hotspots`;
- clue object highlighting;
- rain, smoke, embers, fire glow, flash, camera push, light shake, and fade transitions;
- scene refresh when `snapshot` changes.

Phaser should not handle:

- long Chinese dialogue text;
- free text input;
- evidence selection;
- clue detail panels;
- people/dossier panels;
- markdown or rich text rendering;
- AI calls;
- FastAPI calls;
- clue release logic;
- stage transitions;
- ending resolution;
- global game state.

## React + Phaser Communication

Use React as the bridge between Phaser and FastAPI.

Expected P0 flow:

```text
Player clicks a Phaser hotspot
  -> Phaser emits hotspot:clicked
  -> PhaserStage calls onInspect(sceneId, hotspotId, clueId)
  -> App.tsx calls /api/investigate
  -> backend updates rules/state and returns the result
  -> App.tsx syncs the session snapshot
  -> PhaserStage emits snapshot:update to MainScene
  -> MainScene refreshes background, NPCs, hotspots, and effects
```

Lifecycle requirements:

```text
Create Phaser.Game once when PhaserStage mounts.
Destroy it with game.destroy(true) when PhaserStage unmounts.
Do not create a new Phaser.Game on every React render.
On snapshot changes, emit snapshot:update rather than rebuilding the whole game.
Remove game.events listeners in React cleanup functions.
```

P0 can infer stage feedback from existing data:

- `new_clues.length > 0` -> clue highlight, flash, camera push.
- `scene_id` changed -> fade transition.
- `current_stage` changed -> darken, camera push, title cue.
- NPC emotion changed -> shake, dim, or step animation.
- ending reached -> fade before `EndingPanel`.

P1 can add a backend-provided `stage_cue` field:

```ts
type StageCue = {
  focusHotspotId?: string;
  focusNpcId?: string;
  effects?: Array<'rain' | 'smoke' | 'embers' | 'flash' | 'camera_push' | 'shake'>;
  highlightedClueIds?: string[];
  transition?: 'fade' | 'cut' | 'darken';
};
```

Do not block P0 on `stage_cue`; use frontend inference first.

## Backend Architecture

Current important backend areas:

- `backend/app/main.py` wires the FastAPI app.
- `backend/app/routers/game.py` exposes health, dynasty, identity, session, dialogue, investigate, deduction, choice, ending, and RAG preview routes.
- `backend/app/routers/visual.py` exposes visual asset status, generation, bootstrap, and asset routes.
- Stage 15 may add `backend/app/routers/scripts.py` for generated script jobs, validation, visual generation, and generated session startup.
- `backend/app/services/game_engine.py` is the main rule/state engine.
- `backend/app/services/dialogue_orchestrator.py`, `script_bound_chat.py`, `supervisor.py`, `repair_agent.py`, `rag_retriever.py`, `visual_prompt_agent.py`, and `history_echo_generator.py` support the controlled AI narrative pipeline.
- Stage 15 planned services include `script_generation_service.py`, `script_supervisor.py`, `script_import_service.py`, `script_job_store.py`, `image_quality_gate.py`, `hotspot_calibration_service.py`, and `quote_pool.py`.
- `backend/data/` contains structured dynasty, event, NPC, clue, relationship, visual, rule, and RAG source data.

The backend remains the authority for secrets, AI calls, game state, rules, clue release, NPC permissions, consistency supervision, repair, visual quality gates, hotspot coordinate approval, and ending resolution.

Actual frontend-facing routes currently include:

```text
GET  /api/health
GET  /api/dynasties
GET  /api/roles
GET  /api/player-identities
POST /api/player-identity/validate
POST /api/session/start
GET  /api/session/{session_id}
POST /api/investigate
POST /api/dialogue
POST /api/deduction/submit
POST /api/choice
POST /api/ending/resolve
GET  /api/visual/status
POST /api/visual/generate
GET  /api/visual/assets/{asset_id}
```

Stage 15 planned frontend-facing routes:

```text
POST /api/scripts/generate
GET  /api/scripts/jobs/{job_id}
GET  /api/scripts/{script_id}
POST /api/scripts/{script_id}/validate
POST /api/scripts/{script_id}/visuals/generate
POST /api/session/start-generated
```

P0 route compatibility:

- `POST /api/session/start` keeps the Ming fixed demo path.
- `POST /api/scripts/generate` accepts Northern Song and Late Tang only.
- `dynasty_id=ming` must return `AI_GENERATION_DISABLED_FOR_STABLE_DEMO` unless an explicit development feature flag is enabled.
- empty keywords must return `KEYWORDS_REQUIRED`.

## Core Gameplay Rules

The clue system is P0 and must remain gameplay state, not display-only text. First appearances of discoverable clues use red highlight text; clicking or investigating adds or opens the clue. Clues should affect state through flags, trust, scores, deductions, stage transitions, and ending eligibility.

The main Ming case uses stages equivalent to:

```text
intro -> investigation -> reversal -> choice -> ending
```

Key NPCs are the bookshop owner Xu, engraver A-Shen, failed scholar Gu Wen, low-ranking Jinyiwei officer Lu Zheng, plus an offscreen superior as pressure source. Endings include self-preservation, order, truth, tragedy, and hidden outcome.

`ConsistencySupervisor` is a central safety/control component. It should reject or repair AI output with wrong-dynasty artifacts, role-permission violations, spoilers, personality drift, clue conflicts, stage jumps, risky procedural detail, invalid JSON, or visible non-Chinese player-facing text.

Generated scripts add a higher-level `ScriptSupervisor`. It must reject or repair broken clue chains, unreachable stages or endings, NPC knowledge leaks, weak player permissions, invalid generated identities, missing visual requirements, missing hotspot positions, and any generated content that conflicts with the selected dynasty.

## Visual Direction

Visual generation is P0. The visual style is low-saturation Chinese historical suspense, dark visual-novel UI, rain/fire/smoke atmosphere, and no modern or wrong-dynasty elements.

Current visual decision: the main game scene should be generated as one integrated image per location, with the active NPC(s), historical place, and clue-bearing objects in the same prompt and the same rendered perspective. Do not treat the main stage as a background with large NPC cutouts pasted on top. Example intent: "generate Xu the bookshop owner in the Ming bookshop front hall, with bookcases, shelves, the ledger desk, old book box, red seal paper corner, and doorpost watch mark visible as clue-bearing scene elements." The clickable game layer should sit over this integrated image as hotspot/NPC hit targets.

Phaser should make those visual assets feel like a game stage:

- backgrounds fill the main stage;
- NPCs are already part of the generated scene image; Phaser may add subtle hit targets or focus brackets, but should not duplicate them as large pasted portraits on the main stage;
- hotspots are discoverable but not noisy;
- important clue feedback is visible immediately;
- scene transitions make state changes legible;
- React dialogue and dossier UI remain readable above or beside the stage.

Generated script visuals must additionally include:

- one `visual_style_guide` per generated script;
- `appearance_lock` for every main NPC;
- `era_feature_checklist` for every generated scene;
- structured hotspot positioning using normalized `anchor_point` and `bbox`;
- `ImageQualityGate` approval before an image counts as complete.

Placeholder images, blank images, fallback images, old cached images, wrong-style images, wrong-dynasty images, missing-clue images, or character-inconsistent images must not pass Stage 15 acceptance. They should trigger prompt repair and image regeneration. If required images cannot pass after retries, mark the job `visual_blocked` or failed rather than entering formal gameplay.

## Implementation Priority

Current priority is Stage 15 generated-script expansion while preserving the playable Ming demo path:

```text
Ming fixed demo still starts and plays
Northern Song / Late Tang show keyword generation entry
DeepSeek generates ScriptPackage with multi-round refinement
backend job steps drive real frontend progress graph
required images pass ImageQualityGate
hotspots are calibrated on approved images
generated overview and generated identity selection use ScriptPackage data
start-generated creates a playable generated session
investigate/dialogue/clue/sidebar/ending flow still works
build and tests pass
```

For Stage 15 work, verify at minimum:

- `cd frontend; npm run build`;
- `cd backend; python -m pytest`;
- a browser smoke test that starts the Ming fixed demo;
- a browser smoke test that runs Northern Song or Late Tang through keyword generation, progress, overview, identity selection, and at least one generated hotspot click;
- no regression in `DialoguePanel`, `ClueSidebar`, or `EndingPanel`;
- no visible English user-facing text;
- no API key leakage;
- no placeholder or failed image marked as approved.

Keep changes scoped. Do not combine generated-script implementation with unrelated UI redesign, state-management migration, Ming storyline rewrites, or broad technology swaps.

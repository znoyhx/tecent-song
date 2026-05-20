# CODEBUDDY.md

This file provides guidance to CodeBuddy when working with code in this repository.

## Current Repository State

This repository is no longer documentation-only. It contains a working Stage 1 mock implementation of 《史隙》:

- `docs/PRD.md` defines the product, gameplay, AI/RAG/state-machine constraints, and the new Phaser stage target.
- `frontend/` contains a Vite + React + TypeScript demo frontend.
- `backend/` contains a FastAPI mock demo backend with game flow, clue rules, visual asset routes, dialogue orchestration, supervisor logic, and tests.
- `assets/` contains generated or prepared visual assets.

The current playable direction is still centered on the Ming dynasty bookshop manuscript-burning case. Northern Song and Late Tang should remain lightweight preview entries until the Ming loop is stable.

## Commands

Run commands from the repository root unless otherwise noted.

- `cd frontend; npm run dev` — start the Vite frontend.
- `cd frontend; npm run build` — type-check and build the frontend.
- `cd backend; python -m uvicorn app.main:app --reload` — start the FastAPI backend on the default development port.
- `cd backend; python -m pytest` — run backend tests.
- `rg <term>` or `rg --files` — preferred search commands for code and docs.

When Phaser is implemented, install it in `frontend/` with `npm install phaser` and confirm `frontend/package.json` before relying on the dependency.

## Product Direction

《史隙》 is an AI-driven historical suspense branching narrative web game, not a plain history chatbot or RAG Q&A system. The MVP should deliver one complete playable demo:

```text
Ming dynasty / bookshop apprentice / bookshop manuscript-burning case
```

The user loop is:

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
- NPC portrait/silhouette placement from `snapshot.scene_npcs`;
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
- `backend/app/services/game_engine.py` is the main rule/state engine.
- `backend/app/services/dialogue_orchestrator.py`, `script_bound_chat.py`, `supervisor.py`, `repair_agent.py`, `rag_retriever.py`, `visual_prompt_agent.py`, and `history_echo_generator.py` support the controlled AI narrative pipeline.
- `backend/data/` contains structured dynasty, event, NPC, clue, relationship, visual, rule, and RAG source data.

The backend remains the authority for secrets, AI calls, game state, rules, clue release, NPC permissions, consistency supervision, repair, and ending resolution.

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

## Core Gameplay Rules

The clue system is P0 and must remain gameplay state, not display-only text. First appearances of discoverable clues use red highlight text; clicking or investigating adds or opens the clue. Clues should affect state through flags, trust, scores, deductions, stage transitions, and ending eligibility.

The main Ming case uses stages equivalent to:

```text
intro -> investigation -> reversal -> choice -> ending
```

Key NPCs are the bookshop owner Xu, engraver A-Shen, failed scholar Gu Wen, low-ranking Jinyiwei officer Lu Zheng, plus an offscreen superior as pressure source. Endings include self-preservation, order, truth, tragedy, and hidden outcome.

`ConsistencySupervisor` is a central safety/control component. It should reject or repair AI output with wrong-dynasty artifacts, role-permission violations, spoilers, personality drift, clue conflicts, stage jumps, risky procedural detail, invalid JSON, or visible non-Chinese player-facing text.

## Visual Direction

Visual generation is P0. The visual style is low-saturation Chinese historical suspense, dark visual-novel UI, rain/fire/smoke atmosphere, and no modern or wrong-dynasty elements.

Phaser should make those visual assets feel like a game stage:

- backgrounds fill the main stage;
- NPCs stand in readable positions;
- hotspots are discoverable but not noisy;
- important clue feedback is visible immediately;
- scene transitions make state changes legible;
- React dialogue and dossier UI remain readable above or beside the stage.

## Implementation Priority

Prioritize the playable Ming demo path:

```text
backend running
frontend running
session start
PhaserStage P0
hotspot click -> /api/investigate
dialogue and evidence presentation unchanged
clue sidebar unchanged
stage progression unchanged
ending unchanged
build and tests passing
```

For Phaser work, verify with:

- `cd frontend; npm run build`;
- a browser smoke test that starts a session and clicks at least one Phaser hotspot;
- no regression in `DialoguePanel`, `ClueSidebar`, or `EndingPanel`;
- `cd backend; python -m pytest` if backend contracts or data are touched.

Keep the change small. Do not combine Phaser integration with unrelated UI redesign, state-management migration, backend AI changes, or content rewrites.

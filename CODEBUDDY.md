# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

## Current repository state

This repository is currently a documentation-first project. No `README.md`, `AGENTS.md`, existing `CODEBUDDY.md`, `CLAUDE.md`, Cursor rules, Copilot instructions, package manifests, backend source, frontend source, or test files were found. The product and technical direction are defined mainly in `docs/PRD.md`; image-generation API reference notes are in `docs/help/Imagegenerate.md`.

## Commands

Active build/lint/test commands do not exist yet because the repository contains only docs. When implementation files are added, update this section with the exact scripts from the new manifests.

- `Get-ChildItem -Force -Recurse -File` — Windows PowerShell command to inspect all repository files, including hidden rule/config files, before assuming project structure.
- `python -m pytest backend/tests` — Planned backend test command once `backend/tests/` from the PRD exists; should cover AI connectivity, RAG retrieval, agents, supervisor, and visual prompts.
- `python -m pytest backend/tests/test_deepseek_connection.py` — Planned single-test command for verifying the backend can call the configured DeepSeek model and parse a real response.
- `python -m uvicorn app:app --reload` — Likely FastAPI development command after `backend/app.py` exists; run from `backend/` and adjust module path if implementation differs.
- `npm run dev` — Planned frontend development command after React/Vite or equivalent tooling exists; confirm in `package.json` before use.
- `npm run build` — Planned frontend production build command after `package.json` exists; confirm the actual script name before use.

## High-level architecture

`docs/PRD.md` defines the product as 《史隙》, an AI-driven historical suspense branching narrative web game, not a plain history chatbot or RAG Q&A system. The MVP should deliver one complete playable demo: Ming dynasty / bookshop apprentice / bookshop manuscript-burning case. Northern Song and Late Tang are planned as lighter dynasty-entry demonstrations rather than equal-scope stories.

The intended user loop is visual-novel-style investigation plus reasoning-game clue management: choose dynasty and identity, start a generated historical event world, read a scene with key visual/background, click red-highlighted clues, collect them in a side clue panel, question NPCs, present evidence, combine clues, make irreversible choices, and resolve into multiple endings. The UI direction is a full-screen visual novel stage with scene background, NPC silhouettes/portraits, a bottom dialogue box, top status overlay, action buttons, and a collapsible clue/person/goal panel.

The PRD’s technical stack recommendation is `React + TypeScript` frontend, `Tailwind CSS` styling, `Python FastAPI` backend, `DeepSeek API` for generation/dialogue/supervision, `ChromaDB` for vector retrieval, `SQLite` for structured game state/logs, and JSON/Markdown for editable seed content. Deployment is not implemented; PRD options include static frontend hosting and a backend on CloudBase, Cloud Studio, lightweight server, or similar.

The backend is expected to be the authority for secrets, AI calls, game state, rules, and consistency checks. Planned API surface includes `POST /api/session/start`, `POST /api/player/action`, `POST /api/npc/dialogue`, `POST /api/clue/inspect`, `POST /api/clue/combine`, `POST /api/ending/resolve`, `POST /api/visual/prompt`, and `GET /api/session/{session_id}`.

The core runtime pipeline should be rule-constrained rather than free-form AI storytelling: frontend action → FastAPI → `GameStateManager` → world/event/story services → `RAGRetriever` → AI agent output → `ConsistencySupervisor` → optional `RepairAgent` → state/clue/ending managers → frontend response. AI is responsible for world detail, NPC wording, emotional/action flavor, visual prompts, and history-echo prose; code and rules must control clue release, stage transitions, score changes, and ending eligibility.

The PRD’s planned backend module layout is `backend/app.py`, `backend/config.py`, and `backend/services/` modules for `deepseek_client`, `rag_retriever`, `world_builder`, `relationship_graph_agent`, `event_generator`, `story_director`, `npc_dialogue_agent`, `consistency_supervisor`, `repair_agent`, `clue_manager`, `ending_resolver`, `history_echo_generator`, and `visual_prompt_agent`. Planned data folders include `data/dynasties`, `rules`, `events`, `npcs`, `clues`, `relationships`, `visuals`, and `rag_sources`; runtime storage includes `db/game.sqlite`, `db/chroma`, and AI call logs under `logs/`.

Content architecture centers on a structured case package. The main Ming case uses five stages: `stage_1_intro` (night fire), `stage_2_investigation` (conflicting statements), `stage_3_reversal` (burned material is not just banned writing but grain-ledger evidence), `stage_4_choice` (evidence versus survival), and `stage_5_ending` (historical echo). Key NPCs are the bookshop owner Xu, engraver A-Shen, failed scholar Gu Wen, low-ranking Jinyiwei officer Lu Zheng, plus an offscreen superior as pressure source. Endings include self-preservation, order, truth, tragedy, and hidden outcome.

The clue system is P0 and should be modeled as gameplay state, not display-only text. First appearances of discoverable clues use red highlight text; clicking adds or opens the clue. Clues have IDs, type, source scene/NPC, display text, detail, historical basis, reliability, unlock effects, related clues, ending effects, and discovered status. Clue combinations produce new flags and score/risk changes. NPC dialogue should depend on discovered clues, player action type, current stage, role, trust, relationship graph, and RAG context.

The RAG/knowledge layer exists to keep generated content historically credible. PRD recommends `ChromaDB + SQLite + JSON`, with source metadata containing dynasty, source type, source level, title, note, topic, rule type, severity, and content. Use S/A-level materials for institutions, official posts, legal/military details, and documents; use B/C-level materials for atmosphere and daily-life details. RAG is an internal guardrail, not the main user-facing feature.

`ConsistencySupervisor` is a central safety/control component. It should reject or repair AI output with wrong-dynasty artifacts, role-permission violations, spoilers, personality drift, clue conflicts, stage jumps, risky procedural detail, or invalid JSON. Supervisor output should be structured with `pass`, `issues`, and `repair_instruction`; failed output should go through `RepairAgent` or deterministic fallback text.

AI logging is part of the demo proof. Each call should record call ID, timestamp, module, configured model, input summary, raw prompt path, raw response path, latency, success, and supervisor result. Logs are intended for route/demo evidence that AI is actually connected.

Visual generation is P0. `VisualPromptAgent` should produce prompts for key visual, dynasty concept images, scene backgrounds, NPC silhouettes/portraits, clue images, and turning-point illustrations using a unified style: low-saturation Chinese historical suspense, dark visual-novel UI, rain/fire/smoke atmosphere, and no modern or wrong-dynasty elements. `docs/help/Imagegenerate.md` documents SiliconFlow image generation: `POST https://api.siliconflow.cn/v1/images/generations`, bearer auth, model-specific parameters, and image URLs expiring after one hour.

When implementing, prioritize the playable Ming demo path: project skeleton and AI connectivity, structured Ming data and RAG ingestion, world/relationship/event generation, intro scene, clue highlighting/sidebar, NPC dialogue with evidence presentation, clue combination, state transitions, supervisor/repair, endings, history echo, and visual prompts. Keep Northern Song and Late Tang as lightweight selectable previews until the Ming case loop is complete.

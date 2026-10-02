# ADR-0000 — Initial Foundational Decisions

> **Status:** Accepted
> **Date:** 2026
> **Deciders:** Project Owner
> **Context:** First session gap analysis revealed four foundational questions that block Phase A execution. This ADR records the resolutions so that AI agents and human contributors can proceed without ambiguity.

---

## Summary of Decisions

| # | Topic | Decision |
|---|---|---|
| 1 | License | **AGPL-3.0 + Dual License** |
| 2 | Visual Palette | **AI-authored ADR with three proposals; human decides** |
| 3 | Product Identity | **IDE Master** (canonical name everywhere) |
| 4 | AI Adapter Strategy | **Vendor-neutral via `httpx` now; full ModelAdapter in Phase D** |

---

## Decision 1 — License

**Chosen:** AGPL-3.0 for the open-source core + a separate Commercial License for enterprise features.

**Why:**
- Aligns with `PROJECT_CONSTITUTION.md` §7, Phase A, item 8.
- Enables community growth and contribution.
- Preserves a path to commercial revenue via dual licensing.
- The current `license.txt` (proprietary HPR EULA) **contradicts the constitution** and must be replaced.

**Consequences:**
- `license.txt` will be replaced with `LICENSE` (AGPL-3.0 full text).
- A new `LICENSE-COMMERCIAL.md` will be added (commercial terms, to be drafted).
- The README's License section must be updated to match reality.
- Any third-party code vendored in the repo (e.g. `vis-network.min.js`) must be audited for AGPL compatibility.

**Task Owner:** Phase A, Task 1.

---

## Decision 2 — Visual Palette

**Chosen:** Defer the final decision to a dedicated ADR (`ADR-0003 — Design Tokens v1`) authored by the AI, presenting **three concrete proposals** with trade-offs.

**Why:**
- Two palettes currently coexist and conflict:
  - `theme_manager.py` / `MyTheme.json` → Catppuccin-like dark (`#1a1c23`, `#89b4fa`, `#4fd1c5`, `#ffd700`)
  - `README.md` "Visual Identity" → `#0D47A1` / `#FFB300` / `#F5F7FA` / `#1A1A2E`, font *Inter*
- This is a design decision that benefits from structured comparison, not a coin flip.
- The AI has full context of the codebase and can propose options grounded in reality.

**Consequences:**
- Phase A, Task 4 will include an ADR-0003 with three proposals.
- The human (project owner) will review and pick one.
- Only after that selection will `design/tokens.json` be authored.

**Task Owner:** Phase A, Task 4.

---

## Decision 3 — Product Identity

**Chosen:** **IDE Master** is the canonical product name. The name `CodeSaver` is deprecated.

**Why:**
- The constitution (`PROJECT_CONSTITUTION.md` §1.1) already declares "IDE Master" as the official name.
- Current codebase has identity drift across multiple locations:
  - `run.py` → `HPR.CodeSaver.IDE.v4.2`
  - `main.py` → `"Code Saver - IDE Master v4.0"`
  - Python package → `codesaver`
  - README → "v4.0"
- Multiple competing names confuse users, contributors, and AI agents.
- A single canonical name is required for the "unify" goal of Phase A.

**Consequences:**
- All user-visible strings must say **IDE Master**.
- The app ID becomes a single, stable identifier (exact form to be decided in Task 3; proposed: `IDEMaster.IDE.v4` or similar — must be human-approved).
- The Python package name `codesaver` **may remain** as an internal name to avoid massive refactoring, but the ADR-0002 (restructure) will document this explicitly. Alternatively, renaming can be scheduled post-restructure.
- All version strings must be unified to a single source of truth (e.g. `__version__` in a single module).
- README, window titles, menus, dialogs, error messages — all must use **IDE Master**.

**Task Owner:** Phase A, Task 1 (documentation) + Task 3 (code identity strings).

---

## Decision 4 — AI Adapter Strategy

**Chosen:** Vendor-neutral approach. Immediate fix uses `httpx` directly; a full `ModelAdapter` abstraction is a Phase D deliverable.

**Why:**
- `codesaver/widgets/ai_tools/worker.py` currently imports `openai`, which is **not** in `requirements.txt` → fresh installs crash.
- `PROJECT_CONSTITUTION.md` §2, Principle 2 (**No vendor lock-in**) prohibits hard-wiring any single AI provider.
- Phase D (Agent Mode) requires a `ModelAdapter` capable of routing to:
  - Local: llama.cpp, Ollama, ONNX Runtime
  - Cloud: OpenAI, Anthropic, Gemini, OpenRouter
- Building the full adapter now is premature; we need a minimal fix to unblock Phase A.

**Consequences:**
- **Immediate (Phase A, Task 1):** Replace the `openai` dependency with a minimal `httpx`-based call that speaks the OpenAI-compatible REST API. This preserves functionality without adding the official `openai` SDK.
- **Deferred (Phase D):** Build a proper `ModelAdapter` interface under `core/ai/` that supports multiple backends. The `httpx` code from Phase A becomes one implementation of that interface.
- The official `openai` Python SDK will **not** be added as a dependency.
- `google-generativeai` and `GitPython` will be **removed** (unused).

**Task Owner:** Phase A, Task 1 (immediate) + Phase D (adapter).

---

## Referenced Principles

From `PROJECT_CONSTITUTION.md` §2:

- Principle 1 — Offline-first
- Principle 2 — No vendor lock-in
- Principle 3 — Privacy by default
- Principle 9 — Absolute lightness (every dependency justified)

---

## Follow-up Actions

| Action | Owner | Task |
|---|---|---|
| Replace `license.txt` with AGPL-3.0 + add `LICENSE-COMMERCIAL.md` | Human | Task 1 |
| Fix README license references | AI | Task 1 |
| Audit vendored `vis-network.min.js` for AGPL compatibility | AI | Task 1 |
| Author `ADR-0003 — Design Tokens v1` with three palette proposals | AI | Task 4 |
| Unify identity strings to "IDE Master" in code | AI | Task 1 + Task 3 |
| Replace `openai` import with `httpx` | AI | Task 1 |
| Remove `google-generativeai` and `GitPython` | AI | Task 1 |
| Build full `ModelAdapter` interface | AI | Phase D |

---

## Notes

- This ADR is intentionally **foundational**. It resolves ambiguity that blocked Phase A.
- Any change to these decisions requires a new ADR that explicitly supersedes this one.
- This ADR does not schedule work; it only resolves conflicts.
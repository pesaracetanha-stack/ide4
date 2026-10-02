# Dependency Justifications

> **Purpose:** Written justification for every dependency, as required by `PROJECT_CONSTITUTION.md` §2, Principle 9 (*Absolute lightness*) and Phase A item 11.
> **Maintained by:** Lead Engineer (AI). Update this file in the same commit as any dependency change.
> **Related ADRs:** [ADR-0000](decisions/0000-initial-decisions.md) (Decision 4), [ADR-0001](decisions/0001-qt-binding-pyside6.md).

---

## 1. Runtime Dependencies (requirements.txt)

| Dependency | Version floor | Justification | Alternatives Rejected |
|---|---|---|---|
| `PySide6` | >=6.5.0 | The entire UI layer (57 modules) is built on it. Official Qt for Python binding, LGPLv3 — compatible with the AGPL-3.0 + Commercial dual license (ADR-0001). QtWebEngine powers the architecture-map view; QtSvg the icon pipeline. | PyQt6 (GPL/commercial-only licensing, see ADR-0001); Tkinter (no WebEngine, no modern theming); Electron/Tauri (rewrite, violates lightness). |
| `pyinstaller` | >=6.0.0 | Build-time only: produces the Windows executable defined by `build.spec`. Not imported at runtime. | Nuitka (much slower builds, heavier), cx_Freeze (weaker OneFile/Qt support). |
| `autopep8` | >=2.0.4 | PEP 8 auto-format feature (`Ctrl+Shift+Alt+F`), imported directly by `codesaver/widgets/code_editor.py`. | Ruff-format (planned to replace this in a later phase per constitution §8.2 — Ruff is already mandated for *linting*; replacing the *formatter integration* is deferred to avoid feature churn in Phase A). |
| `httpx` | >=0.27 | AI chat transport: `codesaver/widgets/ai_tools/worker.py` calls any OpenAI-compatible REST endpoint (OpenAI, Groq, Gemini via its OpenAI-compat endpoint, local llama.cpp/Ollama servers) through it. Chosen per ADR-0000 Decision 4 for vendor neutrality. Sync `Client` with timeout + transport-level retries + explicit 429/5xx retry loop. | `openai` SDK (rejected — vendor SDK for a wire protocol we can speak directly, see ADR-0000 D4); `requests` (no first-class timeout/retry semantics per request, heavier); `urllib` (stdlib, but manual and error-prone). |

## 2. Removed Dependencies (this task)

| Dependency | Reason for Removal |
|---|---|
| `google-generativeai` | **Never imported anywhere in the codebase** (verified by AST scan). A cloud-vendor SDK — dead weight that also contradicts Principle 1 (Offline-first) and Principle 2 (No vendor lock-in). |
| `GitPython` | **Never imported anywhere.** Git operations go through `subprocess` calls to the `git` binary in `codesaver/core/git_manager.py`, which is the correct zero-dependency approach. |

## 3. Excluded by Decision

| Dependency | Decision |
|---|---|
| `openai` | **Will not be added** (ADR-0000 Decision 4). The wire protocol is implemented directly via `httpx` in `chat_completions()`. The official SDK adds a large dependency tree for a single REST call, and hard-wires one vendor's client semantics. Revisit only inside the Phase D `core/ai/` ModelAdapter design. |

## 4. Vendored Assets Audit (ADR-0000 follow-up)

| Asset | Size | Version | License | AGPL-3.0 Compatible? |
|---|---|---|---|---|
| `codesaver/templates/assets/vis-network.min.js` | 652 KB | 10.1.2 | Apache-2.0 **or** MIT (dual, per embedded header) | **Yes** — both licenses are permissive and GPL-compatible. The license/copyright header is embedded at the top of the file and must be preserved. |
| `codesaver/templates/graph_template.html` | ~25 KB | n/a (project-authored) | Project code | Yes — authored in-repo. |

**Action for Task 3:** when files move to `resources/`, keep the vis-network header intact and add a `resources/templates/assets/NOTICE` recording upstream source (`https://visjs.github.io/vis-network/`), version, and license choice.

## 5. Known Gaps — Undeclared Imports (discovered during Task 1, NOT fixed here)

An AST scan of all modules on 2026-10-02 found imports that are **not declared** in `requirements.txt`. They are pre-existing issues, documented here for transparency; declaration/removal decisions belong to Task 2 (`pyproject.toml`) and later cleanup:

| Import | Imported by | Classification | Disposition |
|---|---|---|---|
| `networkx` | `codesaver/core/graph_analyzer.py:7` | **Runtime** (architecture graph analysis) | Must be declared in Task 2 (or the analyzer reimplemented without it — needs an ADR; it is a heavy dependency). |
| `jedi` | `codesaver/core/lsp_provider.py` | **Runtime** (Python LSP) | Must be declared in Task 2. Already listed in `build.spec` hiddenimports, confirming it is a real runtime need. |
| `win32con`, `win32gui` (pywin32) | `codesaver/main.py:101-102` | **Runtime, Windows-only**, guarded by `sys.platform == 'win32'` + try/except | Must be declared as a platform-conditional dependency (`pywin32; sys_platform == 'win32'`) in Task 2. |
| `pytest`, `pytest-qt` | `codesaver/tests/*` | **Dev-only** | Deferred to Task 2 dev dependency group (approved by project owner, Task 1 session). |

**Test-environment note:** running the suite additionally required system libraries `libEGL.so.1` and `libXtst.so.6` on a bare Linux container — CI images in Task 5 must include them.

## 6. Dependency Change Protocol

1. Any dependency addition, removal, or version-floor change requires a justification row in this file **in the same commit**.
2. Alternatives considered must be recorded (column 4).
3. New *runtime* dependencies additionally require an ADR when they affect architecture (constitution §0.7).

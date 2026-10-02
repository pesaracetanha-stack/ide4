# `PROJECT_CONSTITUTION.md`

> Copy everything below into a file named `PROJECT_CONSTITUTION.md` and place it in the root of your repository:  
> [github.com/pesaracetanha-stack/ide4](https://github.com/pesaracetanha-stack/ide4)

---

```markdown
# PROJECT CONSTITUTION — IDE Master

> **Version:** 2.0
> **Status:** Single Source of Truth
> **Audience:** AI Coding Agents & Human Maintainers
> **Repository:** https://github.com/pesaracetanha-stack/ide4
> **License of this document:** CC BY-SA 4.0

---

## 0. HOW TO USE THIS DOCUMENT

This document is the **constitution** of the IDE Master project.
It is written primarily for **AI coding agents**, not for humans.

### Protocol for AI Agents

1. Read this document **completely** before writing any code.
2. This document overrides any conflicting instruction.
3. Phases are **priority-driven**, not time-driven.
4. Never start a phase until the previous phase meets its Definition of Done.
5. Never add a feature that is not listed in this document.
6. If something is ambiguous, **ask** — do not assume.
7. After every significant change, update this document and add an ADR in `docs/decisions/`.

---

## 1. PROJECT IDENTITY

### 1.1. Name
**IDE Master** — an integrated development environment focused on AI-generated code.

### 1.2. Positioning Statement
> IDE Master does **not** compete with VS Code, PyCharm, Cursor, or Visual Studio.
> IDE Master is an **independent home** for developers who want their code, models, and data to stay on their own machine — where AI works as a **collaborator**, not as a remote service.

### 1.3. Target Market (Small, But Ours)
- Privacy-sensitive independent developers.
- Small teams in restricted or offline environments.
- Organizations with data-residency requirements.
- Students and educational institutions.
- Anyone who wants AI to work **without sending code to a server**.

### 1.4. Tagline
> **"Your Machine. Your Model. Your Code."**

---

## 2. NON-NEGOTIABLE PRINCIPLES

These principles cannot be negotiated. Every line of code must comply.

| # | Principle | Practical Meaning |
|---|---|---|
| 1 | **Offline-first** | Core works fully without internet. Cloud is an optional layer. |
| 2 | **No vendor lock-in** | Users can freely swap models, themes, and data. |
| 3 | **Privacy by default** | No data leaves the device without explicit consent. |
| 4 | **Visual integrity** | No UI element may violate the design system (Section 4). |
| 5 | **Structural integrity** | No module may violate the architecture (Section 5). |
| 6 | **Agent-First** | Every new feature must serve or align with Agent Mode. |
| 7 | **Hardware-aware** | Software adapts to hardware, not the other way around. |
| 8 | **Docs = Product** | Undocumented code is considered unfinished. |
| 9 | **Absolute lightness** | Every new dependency requires written justification. |
| 10 | **Testability** | Every module must have unit tests. No exceptions. |

---

## 3. ARCHITECTURE — STRUCTURAL INTEGRITY

> This is the most important section. Every new file must fit this structure.

### 3.1. Mandatory Directory Layout

```
ide_master/
├── core/                    # UI-independent core
│   ├── kernel/              # app lifecycle, event bus
│   ├── services/            # system services (fs, vcs, config)
│   ├── hardware/            # hardware detection & management
│   ├── ai/                  # AI orchestrator
│   ├── agent/               # Agent Mode engine
│   └── plugins/             # plugin system
│
├── editor/                  # editor engine (Monaco / CodeMirror)
│   ├── language/            # LSP integration
│   ├── syntax/              # highlighting, folding
│   └── commands/            # command palette, actions
│
├── ui/                      # user interface layer
│   ├── design/              # design tokens, theme engine
│   ├── components/          # base components (Button, Panel, …)
│   ├── layouts/             # standard layouts
│   ├── panels/              # main panels (Explorer, Terminal, …)
│   └── views/               # full pages
│
├── features/                # functional features
│   ├── time_machine/        # automatic versioning
│   ├── project_exporter/    # PDF/TXT/HTML export
│   ├── debugger/            # DAP integration
│   ├── terminal/            # integrated terminal
│   └── notebook/            # Jupyter support
│
├── platform/                # system layer
│   ├── io/                  # files, network, storage
│   ├── security/            # sandbox, permissions
│   └── telemetry/           # optional, off by default
│
├── resources/               # icons, fonts, themes, translations
├── tests/                   # unit, integration, e2e
├── docs/                    # technical documentation
└── tools/                   # build & CI scripts
```

### 3.2. Mandatory Structural Rules

1. **Strict layering:** `ui` may use `core`; `core` must never import from `ui`.
2. **Single responsibility:** if a file exceeds 300 lines, it must be split.
3. **Interface contract:** modules communicate only through declared interfaces, not direct imports.
4. **Central Event Bus:** modules communicate via events, not direct calls.
5. **Dependency Injection:** no class constructs its own dependencies.
6. **No logic in UI:** all logic lives in `core` or `features`; UI only renders.
7. **Config separate from code:** every configurable value lives in config files, never hardcoded.
8. **No absolute paths:** all paths are relative and resolved via `PathService`.

### 3.3. Module Lifecycle

Every new module must go through:

```
1. Define interface in core/interfaces/
2. Implement in the correct location (core/ or features/)
3. Register in ServiceRegistry
4. Write unit test
5. Document in docs/modules/
6. Add to changelog
```

---

## 4. DESIGN SYSTEM — VISUAL INTEGRITY

> **Golden rule:** No color, spacing, font, or animation may be hardcoded. Everything comes from design tokens.

### 4.1. Design Tokens (Mandatory)

All visual values are defined in `design/tokens.json`:

```json
{
  "color": {
    "bg": { "primary": "...", "secondary": "...", "elevated": "..." },
    "text": { "primary": "...", "muted": "...", "inverse": "..." },
    "accent": { "default": "...", "hover": "...", "active": "..." },
    "semantic": { "success": "...", "warning": "...", "error": "...", "info": "..." }
  },
  "space": { "xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32 },
  "radius": { "sm": 4, "md": 8, "lg": 12 },
  "font": {
    "family": { "ui": "...", "code": "..." },
    "size": { "xs": 11, "sm": 12, "md": 14, "lg": 16, "xl": 20 },
    "weight": { "normal": 400, "medium": 500, "bold": 700 }
  },
  "shadow": { "sm": "...", "md": "...", "lg": "..." },
  "motion": {
    "duration": { "fast": 100, "normal": 200, "slow": 350 },
    "easing": { "standard": "...", "emphasized": "..." }
  }
}
```

### 4.2. Visual Rules (Mandatory)

1. **Never hardcode a color.** Use tokens only.
2. **Spacing only from `space` scale** (4, 8, 16, …).
3. **Font sizes only from `font.size` scale.**
4. **Animations only from `motion.duration` and `motion.easing`.**
5. **Every component defines three states:** default, hover, disabled.
6. **Every component is tested in two themes:** light and dark.
7. **Every page uses a standard layout.**
8. **All icons come from one set** (Lucide or Tabler). No exceptions.

### 4.3. Theme Engine

- Themes are stored as JSON in `resources/themes/`.
- Compatibility with VS Code theme format is **mandatory**.
- Users can create, import, and export themes.
- Theme changes apply **without restart**.

### 4.4. Standard Layout

```
┌───────────────────────────────────────────────┐
│  Title Bar (custom, draggable)                │
├──────┬──────────────────────────────┬─────────┤
│      │                              │         │
│ Side │       Editor Area            │  Panel  │
│ Bar  │       (split-able)           │ (AI/…)  │
│      │                              │         │
├──────┴──────────────────────────────┴─────────┤
│  Status Bar (info, errors, hardware)          │
└───────────────────────────────────────────────┘
```

No page may deviate from this layout without written justification.

---

## 5. AGENT MODE — ABSOLUTE PRIORITY

> **Agent Mode is the heart of IDE Master. Every other capability is designed to serve it.**

### 5.1. Definition

Agent Mode is a state where AI can:
- Think in multiple steps (plan → act → observe → refine).
- Read, write, and edit files.
- Run terminal commands with user approval.
- Write and run tests.
- Observe errors and self-correct.
- Report its own progress.

### 5.2. Mandatory Architecture

```
┌────────────────────────────────────────────┐
│            Agent Orchestrator              │
│  (Brain: planning, memory, decision)       │
├────────────────────────────────────────────┤
│  Tool Registry                             │
│  ├── FileTool (read/write/edit)            │
│  ├── ShellTool (exec, sandboxed)           │
│  ├── SearchTool (grep, semantic)           │
│  ├── TestTool (pytest runner)              │
│  ├── GitTool (diff, commit)                │
│  └── BrowserTool (optional)                │
├────────────────────────────────────────────┤
│  Memory Layer                              │
│  ├── Short-term (current task)             │
│  ├── Long-term (project knowledge)         │
│  └── Vector Store (RAG, local)             │
├────────────────────────────────────────────┤
│  Approval Gate (human-in-the-loop)         │
├────────────────────────────────────────────┤
│  Model Adapter (local / cloud)             │
└────────────────────────────────────────────┘
```

### 5.3. Agent Mode Requirements

- [ ] **Plan-Act-Observe loop:** every task plans, executes, observes, refines.
- [ ] **Full transparency:** user sees every step and can interrupt.
- [ ] **Approval Gate:** every write or shell execution requires approval (disable-able for advanced users).
- [ ] **Full Rollback:** every Agent change reverts with one click.
- [ ] **Persistent Memory:** Agent stores project memory in SQLite.
- [ ] **Context Engine:** intelligent selection of relevant files (local RAG).
- [ ] **Multi-Agent:** specialized agents (writer, tester, reviewer).
- [ ] **Trace & Replay:** full session recording for review.
- [ ] **Sandbox:** Agent-executed code runs in a restricted environment.
- [ ] **Cost Guard:** track and limit token consumption.

### 5.4. Tool Contract

Every Tool must implement:

```
interface Tool {
  name: string
  description: string
  schema: JSONSchema           // input parameters
  permissions: Permission[]    // fs:read, fs:write, shell, network
  sandboxed: boolean
  execute(params, context): Promise<Result>
  rollback(resultId): Promise<void>
}
```

### 5.5. Implementation Order

1. **Foundation:** Tool Registry + Approval Gate + Trace log.
2. **Core Tools:** File, Shell, Search.
3. **Loop:** Plan → Act → Observe.
4. **Memory:** SQLite + Vector Store.
5. **Context Engine:** local RAG.
6. **Multi-Agent:** specialized agents.
7. **Replay & Audit:** recording and playback.

---

## 6. HARDWARE-AWARE PROCESSING

> **Goal:** the software adapts itself to the user's hardware capability.

### 6.1. Hardware Detection Module

Module `core/hardware/` detects:

| Source | Data |
|---|---|
| **CPU** | architecture (x86_64, arm64), core count, AVX/AVX2/AVX-512 |
| **GPU** | vendor (NVIDIA, AMD, Intel, Apple), model, VRAM, API (CUDA, ROCm, Metal, Vulkan, DirectML) |
| **RAM** | total and free |
| **Storage** | type (SSD/HDD), free space |
| **OS** | version, architecture |
| **NPU** | presence and type (Apple Neural Engine, Intel NPU, …) |

### 6.2. Automatic Backend Router

| Hardware | Backend | Use Case |
|---|---|---|
| NVIDIA + CUDA | **CUDA** | inference, fine-tuning |
| AMD + ROCm | **ROCm** | inference |
| Apple Silicon | **Metal / Core ML** | fast inference |
| Intel + Vulkan | **Vulkan** | inference |
| NPU present | **ONNX Runtime / NPU** | low-power inference |
| CPU only | **llama.cpp with AVX** | light inference |
| None | **Cloud (optional)** | fallback |

### 6.3. Hardware-Aware Rules

1. **Detect at startup** and store in `HardwareProfile`.
2. **Never assume a GPU exists.** Always fallback to CPU.
3. **Show hardware status in Status Bar** (e.g. `GPU: RTX 3060 (12GB) | CUDA 12.1`).
4. **User can manually override the backend.**
5. **Model selection based on VRAM:**
   - 4GB → 3B models with quantization
   - 8GB → 7B models
   - 16GB → 13B models
   - 24GB+ → 30B+ models
6. **Automatic quantization:** Q4_K_M default, Q8 for high precision, Q2 for weak systems.
7. **Memory management:** auto-unload model after idle.
8. **Performance metric:** show tokens/sec in Status Bar.

### 6.4. Required Modules

```
core/hardware/
├── detector.py          # detect CPU/GPU/RAM
├── profiler.py          # build HardwareProfile
├── backend_router.py    # select suitable backend
├── vram_manager.py      # manage VRAM
└── benchmarks.py        # performance tests
```

---

## 7. PRIORITY-DRIVEN PHASES (No Time)

> **Rule:** A phase starts only when the previous phase meets its Definition of Done.

---

### PHASE A — Foundation

**Goal:** make the existing project trustworthy, unified, and ready for development.

- [ ] Resolve PyQt6 / PySide6 conflict — pick one, remove the other.
- [ ] Unify folder structure per Section 3.
- [ ] Create `design/tokens.json` and remove all hardcoded visual values.
- [ ] Build `ServiceRegistry` and central `EventBus`.
- [ ] Add `pyproject.toml` + `uv` or `poetry`.
- [ ] Set up `pre-commit` with Ruff + mypy + pytest.
- [ ] Add CI with GitHub Actions.
- [ ] Change license to **AGPL-3.0 + Dual License**.
- [ ] Write `docs/architecture.md`.
- [ ] Reach at least 50% test coverage for core.
- [ ] Remove every dependency without written justification.

**Definition of Done:**
- Project builds, tests pass, CI is green.
- No file lives outside the Section 3 structure.
- All UI uses design tokens.

---

### PHASE B — Unified Visual Layer (Design System)

**Goal:** a complete, reusable design system across the whole app.

- [ ] Implement Theme Engine with light/dark support.
- [ ] Build base component library:
  - Button, IconButton, Input, Textarea, Select
  - Checkbox, Radio, Switch, Slider
  - Tabs, Accordion, Modal, Tooltip, Popover
  - Card, Panel, Divider, Badge
  - Toast, Notification, ProgressBar
  - Tree, List, Table
- [ ] Build standard layout per Section 4.4.
- [ ] Build internal **Storybook** for all components.
- [ ] Implement Status Bar with hardware display.
- [ ] Implement Command Palette.
- [ ] Support **VS Code themes** (import/export).
- [ ] i18n system with Persian and English.
- [ ] RTL support.
- [ ] Standard animations per tokens.

**Definition of Done:**
- Storybook shows all components in both themes.
- No page deviates from the standard layout.
- Theme changes apply without restart.

---

### PHASE C — Professional Editor (Editor Core)

**Goal:** an editor that can be taken seriously.

- [ ] Integrate Monaco or CodeMirror 6.
- [ ] Integrate LSP (pyright + jedi).
- [ ] Autocomplete, go-to-def, find-references, rename symbol.
- [ ] Syntax highlighting for Python, JS, TS, JSON, YAML, Markdown, …
- [ ] Multi-cursor, split view, minimap.
- [ ] Find & Replace with regex.
- [ ] Folding, indentation guides.
- [ ] Auto-save + Time Machine.
- [ ] Git integration (status, diff, commit, branch).
- [ ] Terminal integration (xterm.js or similar).
- [ ] DAP integration (debugpy) for Python.
- [ ] Virtual environment management (venv, poetry, uv, conda).
- [ ] Improve existing **Auto-Creation Magic**.

**Definition of Done:**
- User can fully write, run, and debug a Python project inside the IDE.

---

### PHASE D — Agent Mode (Top Priority)

**Goal:** the heart of IDE Master.

- [ ] Implement `Tool Registry` and `Tool Contract`.
- [ ] Build base Tools: File, Shell, Search, Git, Test.
- [ ] Implement `Approval Gate` with transparent UI.
- [ ] Implement Plan → Act → Observe → Refine loop.
- [ ] Build `Memory Layer`:
  - Short-term (in-memory)
  - Long-term (SQLite)
  - Vector Store (local RAG)
- [ ] Implement `Context Engine` (intelligent file selection).
- [ ] Implement `Trace & Replay`.
- [ ] Implement full `Rollback` for every operation.
- [ ] Implement `Cost Guard`.
- [ ] Implement `Multi-Agent` (writer, tester, reviewer).
- [ ] Sandbox for Agent-executed code.
- [ ] Dedicated Agent Mode panel in UI (per Section 4.4).

**Definition of Done:**
- User can say "add this feature"; the Agent creates files, writes tests, runs them, fixes errors, and reports — with user approval at every step.

---

### PHASE E — Hardware-Aware Runtime

**Goal:** automatically match the user's device capability.

- [ ] Implement `Hardware Detector` (CPU/GPU/RAM/NPU).
- [ ] Implement `Backend Router`.
- [ ] Integrate `llama.cpp` for CPU.
- [ ] Integrate CUDA for NVIDIA.
- [ ] Integrate ROCm for AMD.
- [ ] Integrate Metal for Apple Silicon.
- [ ] Integrate Vulkan for Intel/AMD.
- [ ] Integrate ONNX Runtime for NPU.
- [ ] VRAM management and auto-unload.
- [ ] Automatic model selection based on VRAM.
- [ ] Automatic quantization selection.
- [ ] Show tokens/sec and GPU status in Status Bar.
- [ ] Internal `Benchmarks` for backend selection.
- [ ] Manual override by user.

**Definition of Done:**
- The app performs optimally on any device — from an old laptop to an RTX 4090 workstation — without manual tuning.

---

### PHASE F — Professional Features

**Goal:** make IDE Master a complete tool.

- [ ] **Advanced Time Machine:** branch from snapshot, version comparison.
- [ ] **Advanced Project Exporter:** PDF, HTML, Markdown, ZIP.
- [ ] **Internal Jupyter Notebook.**
- [ ] **Remote Development:** SSH, Docker, WSL.
- [ ] **Team Sync (optional, E2E encrypted).**
- [ ] **Team Prompt Library.**
- [ ] **Automatic Test Generator.**
- [ ] **Automatic Doc Generator.**
- [ ] **Internal AI Code Review.**
- [ ] **Diagram Generator (Mermaid, PlantUML).**
- [ ] **Internal Database Explorer.**
- [ ] **Internal REST/GraphQL Client.**
- [ ] **Professional Diff Viewer.**
- [ ] **Global Search (grep + semantic).**

**Definition of Done:**
- IDE Master is a complete replacement for scattered tools for a professional developer.

---

### PHASE G — Ecosystem & Platform

**Goal:** turn the product into a platform.

- [ ] **Plugin SDK** (JS/TS + Rust + Python).
- [ ] **Plugin Marketplace** with developer payouts.
- [ ] **Public API** for automation.
- [ ] **CLI** (`idemaster` command).
- [ ] **Self-hosted Server** for organizations.
- [ ] **Real-time Collaboration** (Live Share).
- [ ] **Support for other languages:** JS/TS, Go, Rust, C++.
- [ ] **Plugin developer documentation.**
- [ ] **Ambassador Program.**

**Definition of Done:**
- An external developer can build and publish a plugin in one hour.

---

### PHASE H — Enterprise & Scale

**Goal:** presence in large organizations.

- [ ] **SSO / SAML / OIDC.**
- [ ] **Full Audit Log.**
- [ ] **Policy Enforcement.**
- [ ] **On-premise Deployment.**
- [ ] **SLA and dedicated support.**
- [ ] **Custom model fine-tuning for teams.**
- [ ] **Team management dashboard.**

**Definition of Done:**
- A 1000-person organization can deploy IDE Master on its own infrastructure.

---

## 8. CODING RULES (For AI)

### 8.1. General Principles

1. **KISS** — simplest solution that works.
2. **DRY** — but not at the cost of complexity.
3. **YAGNI** — do not build what is not needed.
4. **Readability over cleverness.**
5. **Descriptive naming, no abbreviations.**

### 8.2. Python

- Python 3.11+
- Type hints **mandatory** for all functions.
- Ruff + Black for formatting.
- Google-style docstrings.
- Async/await for I/O.
- Pydantic for structured data.

### 8.3. Frontend (if Tauri/React)

- TypeScript strict mode.
- Functional Components + Hooks.
- State management: Zustand or Jotai (lightweight).
- Styling: CSS Variables from design tokens.

### 8.4. Commits

Format: `type(scope): description`
- `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`

### 8.5. Testing

- pytest for Python.
- Playwright for E2E.
- Every PR must include tests.
- Minimum coverage: 70% (gradually moving to 90%).

---

## 9. DEFINITION OF DONE

A task is done when:

- [ ] Code is written.
- [ ] Tests are written and passing.
- [ ] Documented.
- [ ] Complies with design tokens.
- [ ] Lives in the correct location per Section 3.
- [ ] Does not conflict with Section 2 principles.
- [ ] Logged in changelog.
- [ ] Builds on all three OSes (Linux, macOS, Windows).
- [ ] Reviewed by another AI or human.

---

## 10. AI WORK PROTOCOL

When an AI works on this project:

1. **Read this document completely first.**
2. **Determine the current phase from Section 7.**
3. **Never jump ahead of the current phase.**
4. **Never build a feature outside this document.**
5. **If user request conflicts with this document, remind them of the document first, then proceed only with explicit approval.**
6. **After every change, update this document accordingly.**
7. **Log every major decision in `docs/decisions/` (ADR).**
8. **If ambiguous, ask — do not assume.**

---

## 11. APPENDICES

### 11.1. Important Links
- **GitHub:** https://github.com/pesaracetanha-stack/ide4
- **Issues:** https://github.com/pesaracetanha-stack/ide4/issues
- **Discussions:** https://github.com/pesaracetanha-stack/ide4/discussions

### 11.2. Reference Resources
- VS Code API (for plugin architecture inspiration)
- LSP Specification
- DAP Specification
- llama.cpp, ONNX Runtime, Ollama docs

### 11.3. Glossary

| Term | Meaning |
|---|---|
| Agent Mode | Automated AI execution mode |
| Tool | Capability usable by the Agent |
| RAG | Retrieval-Augmented Generation |
| Design Token | Base visual value |
| ADR | Architecture Decision Record |
| DAP | Debug Adapter Protocol |
| LSP | Language Server Protocol |

---

## 12. IMMEDIATE START CHECKLIST

Before any other work, the AI must:

- [ ] Read this document completely.
- [ ] Inspect the current repository state.
- [ ] Determine the current phase.
- [ ] Produce a gap analysis between current state and the current phase.
- [ ] Propose the first actionable task.
- [ ] Wait for user approval.

---

> **This document is alive.** Every change must be committed to GitHub and its version incremented.
>
> **Current version:** 2.0
> **Repository:** https://github.com/pesaracetanha-stack/ide4
> **License of this document:** CC BY-SA 4.0
```

---


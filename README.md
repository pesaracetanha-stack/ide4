# IDE Master v4.0 🚀  
**Your smart bridge to AI**

IDE Master v4.0 is a hyper-fast, beautifully designed Integrated Development Environment (IDE) engineered by the **HPR** team. It is specifically built for developers who need a seamless, fully offline workspace to integrate and test AI-generated code without relying on heavy cloud platforms.

---

## 🎯 Why IDE Master?
- **Fully Offline**: No internet required, secure, and private.
- **Hyper-Fast**: Designed with low-level optimizations for smooth execution on standard hardware.
- **AI Integrated**: The ultimate tool for testing and debugging AI-generated code.
- **Time-Saving**: Automates file creation, formatting, and version control.
# IDE Master

> **Your Machine. Your Model. Your Code.**

An offline-first, AI-native integrated development environment for developers who want their code, models, and data to stay on their own machine.

---

## What This Is

IDE Master is a **desktop IDE** built for the age of AI-generated code.

It is **not** a competitor to VS Code, PyCharm, Cursor, or Visual Studio.  
It is an independent home for developers who:

- Refuse to send their code to a remote server.
- Want to run their AI models locally whenever possible.
- Value a coherent, predictable visual and structural system.
- Want an **Agent Mode** that writes, tests, and fixes code with human approval at every step.

---

## Core Principles

| # | Principle |
|---|---|
| 1 | **Offline-first** — the core works fully without internet |
| 2 | **No vendor lock-in** — swap models, themes, and data freely |
| 3 | **Privacy by default** — no data leaves your device without consent |
| 4 | **Visual integrity** — every pixel comes from design tokens |
| 5 | **Structural integrity** — every file lives in its designated layer |
| 6 | **Agent-First** — every feature serves Agent Mode |
| 7 | **Hardware-aware** — the app adapts to your GPU, CPU, and NPU |
| 8 | **Docs = Product** — undocumented code is unfinished |
| 9 | **Lightweight** — every dependency must justify itself |
| 10 | **Testability** — every module has unit tests |

---

## Current Status

**Phase:** A — Foundation (in progress)

The project is being restructured into a coherent, professional architecture.  
See [`PROJECT_CONSTITUTION.md`](./PROJECT_CONSTITUTION.md), Section 7 for the full phase roadmap.

---

## Documentation

All project documentation lives in the repository, not in chat.

| Document | Purpose |
|---|---|
| [`PROJECT_CONSTITUTION.md`](./PROJECT_CONSTITUTION.md) | The law of the project. Read this first. |
| [`BOOTSTRAP.md`](./BOOTSTRAP.md) | Entry point for AI agents and new contributors. |
| [`docs/architecture.md`](./docs/architecture.md) | Technical architecture detail. *(pending)* |
| [`docs/design.md`](./docs/design.md) | Design system detail. *(pending)* |
| [`docs/decisions/`](./docs/decisions/) | Architecture Decision Records (ADRs). *(pending)* |
| [`docs/modules/`](./docs/modules/) | Per-module documentation. *(pending)* |

---

## For AI Agents

If you are an AI coding agent working on this project:

1. Read [`BOOTSTRAP.md`](./BOOTSTRAP.md) completely.
2. Then read [`PROJECT_CONSTITUTION.md`](./PROJECT_CONSTITUTION.md) completely.
3. Then use the Activation Prompt in `BOOTSTRAP.md`, Section 5.
4. Do not write any code before completing the above.

---

## For Human Contributors

Before opening a pull request:

1. Read [`PROJECT_CONSTITUTION.md`](./PROJECT_CONSTITUTION.md).
2. Ensure your change fits the current phase.
3. Ensure your change respects the directory layout in Section 3.
4. Ensure your change uses design tokens, not hardcoded values.
5. Ensure every new module has tests.
6. Ensure every significant decision is logged as an ADR.

Pull requests that ignore the constitution will be closed without review.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| UI Framework | PySide6 *(being finalized)* |
| Editor Engine | Monaco or CodeMirror 6 *(planned)* |
| Database | SQLite |
| AI Runtime | llama.cpp, ONNX Runtime, CUDA, ROCm, Metal *(planned)* |
| Packaging | PyInstaller *(being revisited)* |

The stack is defined in [`PROJECT_CONSTITUTION.md`](./PROJECT_CONSTITUTION.md), Section 3.

---

## Roadmap (Priority-Driven, No Time)

| Phase | Focus |
|---|---|
| **A** | Foundation — clean up, unify, CI, license |
| **B** | Design System — unified visual layer |
| **C** | Editor Core — Monaco, LSP, DAP, terminal |
| **D** | **Agent Mode** — top priority |
| **E** | Hardware-Aware Runtime — GPU/CPU/NPU detection |
| **F** | Professional Features — Jupyter, remote dev, exporters |
| **G** | Platform — Plugin SDK, marketplace |
| **H** | Enterprise — SSO, audit, on-premise |

Detailed task lists are in [`PROJECT_CONSTITUTION.md`](./PROJECT_CONSTITUTION.md), Section 7.

---

## License

This project uses a **dual-license model**:

- **AGPL-3.0** for the open-source core.
- **Commercial license** for enterprise features.

See [`LICENSE`](./LICENSE) and [`LICENSE-COMMERCIAL.md`](./LICENSE-COMMERCIAL.md) *(pending)*.

---

## Repository

https://github.com/pesaracetanha-stack/ide4

---

## Tagline

**"Your Machine. Your Model. Your Code."**
---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **Auto-Creation Magic** | By copying the AI code and file path, a simple `Ctrl+S` creates all nested folders and saves the file. |
| **Time Machine (Version History)** | Automatic background snapshots, allowing rollback to previous versions with a single click. |
| **PEP 8 Auto-Formatter** | Integration of `autopep8` for automatic Python code formatting (`Ctrl+Shift+Alt+F`). |
| **Advanced Global Search** | Instant search across the entire project and jump to classes/methods with `Ctrl+Shift+O`. |
| **Project Exporter** | Export the entire project as a `.txt` file to feed to AI, or a `.pdf` for documentation. |
| **Integrated Terminal** | Run scripts and manage virtual environments without leaving the editor. |
| **AI Debugger Assistant** | Automatic error analysis and troubleshooting suggestions. |

---

## 🆚 Competitive Advantages (Why IDE Master stands out?)

| Competitors (VS Code, PyCharm, etc.) | IDE Master |
| :--- | :--- |
| Requires multiple plugins to be installed | **All-in-one** with no extra configuration |
| High RAM and CPU usage | **Lightweight and optimized**, suitable for low-end systems |
| Internet connection required for many features | **Fully offline** and secure |
| Cluttered and complex menus | **Minimalist** and user-friendly design |
| High price (Professional versions) | **Free and open-source** (with custom license) |

> **IDE Master = Power + Simplicity + Speed**

---

## 📦 Technologies Used

- **Programming Language**: Python 3.10+
- **GUI Framework**: PyQt6
- **Database**: SQLite (For versioning and settings)
- **Code Formatter**: autopep8
- **Build System**: PyInstaller (For generating executables)

---

## 🎨 Visual Identity (For Website Design)

- **Primary Color**: `#0D47A1` (Dark Blue) – Symbolizes trust and professionalism
- **Secondary Color**: `#FFB300` (Gold) – Symbolizes creativity and value
- **Background Color**: `#F5F7FA` (Blueish-White) for light mode
- **Text Color**: `#1A1A2E` (Dark Gray)
- **Font**: **Inter** (For optimal readability)
- **Overall Style**: **Minimalist, clean, with ample white space and emphasis on readability**

---

## 📄 Proposed Website Structure

1. **Home**
   - Short introduction with typewriter animation
   - CTA Buttons: "Download for Windows" and "View Demo"
   - Display stats (Downloads, Users, Current Version)

2. **Features**
   - Grid view of all features with icons and brief descriptions
   - Real screenshots of the software

3. **Competitive Advantages (Why IDE Master?)**
   - Comparison table with VS Code and PyCharm
   - Explanation of why the user should download

4. **Docs**
   - Link to the manual (PDF or HTML)
   - Step-by-step getting started guide

5. **Download**
   - Download button for Windows 64-bit
   - Display version changes (Changelog)

6. **Testimonials**
   - Real user reviews (with photo and name)
   - Option to submit a new review (Simple form)

7. **Contact**
   - Contact form (Name, Email, Message)
   - Contact info: Email and social media links

8. **Footer**
   - Quick links (Home, Features, Download, Contact)
   - Copyright GitiArts
   - Social media icons (Links to be added manually)

---

## 🚀 Installation & Setup

# Or download the Windows executable file from the link below
https://gitiarts.ir/idem4/idemv4.zip

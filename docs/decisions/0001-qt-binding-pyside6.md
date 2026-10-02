# ADR-0001 — Qt Binding: PySide6

> **Status:** Accepted
> **Date:** 2026-10-02
> **Deciders:** Project Owner (approved in Task 1 execution plan), Lead Engineer (AI)
> **Context:** Phase A, item 1 — "Resolve PyQt6 / PySide6 conflict — pick one, remove the other."
> **Supersedes:** none (first binding decision; resolves the conflict flagged in the First Session gap analysis)

---

## Decision

**PySide6 is the sole Qt binding for IDE Master.** PyQt6 is permanently excluded from the dependency tree.

## Context

The First Session gap analysis flagged a "PyQt6 / PySide6 conflict." Investigation showed the conflict was **documentation-only**:

- All 57 GUI modules import `PySide6` exclusively; a repository-wide search found **zero** `PyQt6` imports.
- `README.md` ("Technologies Used: GUI Framework: PyQt6") was the only PyQt6 claim in the project.
- `requirements.txt` already declared `PySide6>=6.5.0` and never declared PyQt6.

## Rationale

| Factor | PySide6 | PyQt6 |
|---|---|---|
| License | **LGPLv3** (Qt for Python, by Qt Group) | **GPLv3** or paid Riverbank commercial license |
| Fit with AGPL-3.0 + Commercial dual license (ADR-0000 D1) | Clean: LGPL allows the dual-license model | Problematic: GPLv3 would force single-license AGPL or require a paid commercial license for the dual model |
| Existing code | 57/57 modules already on it | Zero usage |
| API surface | Near-identical to PyQt6 (same Qt API) | — |
| Maintenance | Backed by the Qt Company itself | Backed by Riverbank Computing |

Given identical API surface and an already-100%-PySide6 codebase, licensing is the deciding factor.

## Consequences

1. `README.md` "Technologies Used" corrected to PySide6 (done in this task).
2. `docs/dependencies.md` carries the written justification for PySide6 (constitution §2, principle 9).
3. PyQt6 **must not** be added by any future change; a future ADR would be required to revisit.
4. Any code sample, doc, or CI snippet referencing PyQt6 is a defect.
5. When the Phase A restructure (Task 3) moves widgets into `ui/`, the binding stays PySide6 — this ADR travels with the code.

## Compliance

- Constitution §2, Principle 9 (Absolute lightness): dependency justified in writing. ✔
- Constitution §7, Phase A, item 1: conflict resolved. ✔
- Constitution §0.7 / §10.7: decision logged as ADR. ✔

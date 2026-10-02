# TODO — Identity Drift Backlog (resolved in Task 3)

> **Context:** ADR-0000 Decision 3 declares **IDE Master** the canonical product name; `CodeSaver` is deprecated.
> **Scope:** This file inventories every identity-drift location found in the First Session gap analysis (re-verified 2026-10-02). Code changes are deliberately deferred to **Task 3 (directory restructure)** so that the restructure commit and the identity unification land together, per ADR-0000 D3 ("Task Owner: Task 1 (documentation) + Task 3 (code identity strings)").
> **Rule:** User-visible strings say **IDE Master**. Version strings come from a single source of truth.

## A. Code — app identity

- [ ] `run.py:10` — `app_id = "HPR.CodeSaver.IDE.v4.2"` → single stable identifier (proposed `IDEMaster.IDE.v4`, **needs project-owner approval** per ADR-0000 D3)
- [ ] `codesaver/main.py:43` — `self.setWindowTitle("Code Saver - IDE Master v4.0")`
- [ ] `codesaver/main.py:176` — second `setWindowTitle("Code Saver - IDE Master v4.0")` call
- [ ] `codesaver/tests/test_integration.py:10` — asserts the old title string; **must change in lockstep** with `main.py`
- [ ] Version chaos: `v4.0` (main.py, README header) vs `v4.2` (run.py app id) → introduce single `__version__` in one module, import everywhere

## B. Code — QSettings identities (⚠ renaming migrates user settings; needs a migration note in ADR-0002)

- [ ] `codesaver/main.py:284` — `QSettings("HPR", "CodeSaver")`
- [ ] `codesaver/widgets/welcome_screen.py:299` — `QSettings("HPR", "CodeSaver")`
- [ ] `codesaver/widgets/plugin_panel.py:55` — `QSettings("GitiArts", "CodeSaver_Theme")`
- [ ] `codesaver/widgets/preferences_dialog.py:46,297` — `QSettings("GitiArts", "CodeSaver_Theme")`
- [ ] `codesaver/widgets/ai_tools/settings.py:82` — `QSettings("GitiArts", "CodeSaver_AI")`
- [ ] `codesaver/widgets/ai_tools/settings.py:83` — `QSettings("GitiArts", "CodeSaver_Theme")`
- [ ] `codesaver/widgets/ai_tools/chat_bubbles.py:99,147` — `QSettings("GitiArts", "CodeSaver_Theme")`
- [ ] `codesaver/widgets/welcome_screen.py:42` — `QSettings("GitiArts", "CodeSaver_Theme")`
- [ ] Proposal for Task 3: one `core/services/settings_service.py` owning the org/app constants (constitution §3.2 rule 7 — config separate from code)

## C. Package & repository naming

- [ ] Python package `codesaver/` — ADR-0000 D3: *may remain* as internal name to limit churn; final call recorded in ADR-0002 (restructure) — **needs project-owner approval if renamed**
- [ ] `codesaver/core/splash_data.py` — 263 KB base64 splash with old branding; moves to `resources/` in Task 3, visual refresh coordinated with Task 4 (tokens)
- [ ] `pytest.ini` `testpaths = codesaver/tests` — follows the package decision
- [ ] `build.spec` — references `codesaver_icons`, `run.py`, app metadata; updates with the restructure

## D. Documentation & web presence (stale README era)

- [ ] `README.md:1` — header "IDE Master v4.0 🚀 **Your smart bridge to AI**" (legacy tagline; constitution §1.4 tagline is "Your Machine. Your Model. Your Code.")
- [ ] `README.md:4` — "engineered by the **HPR** team" (legacy attribution; keep only if owner confirms)
- [ ] `README.md` — duplicate "Core Principles" / "Key Features" / "Competitive Advantages" sections from the v4.0 era; consolidate in Task 3's README rewrite
- [ ] `README.md:246` — legacy download link `https://gitiarts.ir/idem4/idemv4.zip`
- [ ] `README.md` "Visual Identity (For Website Design)" — palette `#0D47A1`/`#FFB300`/Inter; **input to ADR-0003 (Design Tokens v1)**, not an identity fix
- [ ] `license.txt` — legacy HPR EULA; replacement with `LICENSE` (AGPL-3.0) is **owner-owned** per ADR-0000 follow-up table

## E. Out of scope for Task 3 (recorded for completeness)

- [ ] `run.py:10-12` — Windows `ctypes.windll` AppUserModelID hack unguarded by `sys.platform` check (robustness, not identity)
- [ ] QSettings org strings ("HPR" vs "GitiArts") also affect **where** settings live on disk per OS — a rename without migration silently resets user themes and API keys

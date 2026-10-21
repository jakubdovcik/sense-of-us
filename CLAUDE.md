# Instructions for Claude Code

This repository is a research project on Ricardo Hausmann's concept of the "sense of us". It profiles how societies define who "we" are by having Claude code them against a codebook, measures reliability, builds a typology, and publishes everything as the **Sense of Us atlas**, a static dashboard deployed to GitHub Pages. Read `docs/FRAMEWORK.md` and `docs/RESEARCH_PLAN.md` before changing anything substantive.

## First session

1. Check `gh auth status`. If not logged in, stop and ask the user to run `gh auth login` themselves. Never handle tokens or passwords.
2. Create a virtual environment, run `pip install -e ".[dev]"`, then `pytest -q`. All tests must pass.
3. Run `sou dashboard --demo` and open `site/index.html` in a browser to confirm the dashboard renders (it needs internet for the chart library).
4. Run `git init -b main`, commit everything with the message `Initial scaffold`, then create a **private** repository and push it with `gh repo create sense-of-us --private --source=. --remote=origin --push`.
5. Before switching on GitHub Pages, ask the user two questions and wait for the answers.
   - The published dashboard is visible to anyone with the link, even when the repository is private. Is that acceptable?
   - GitHub Pages on a private repository needs a paid plan (GitHub Pro, free through the GitHub Student Developer Pack). Does the user have one, or should the repository be made public?
6. If the user agrees, enable Pages with GitHub Actions as the source using `gh api -X POST repos/{owner}/sense-of-us/pages -f build_type=workflow`, run `gh workflow run dashboard.yml`, wait for it with `gh run watch`, and fetch the address with `gh api repos/{owner}/sense-of-us/pages --jq .html_url`.
7. Report the repository URL, the dashboard URL and the test result.

If a workflow fails because an action version is deprecated, update it to the current major version and note the change in `docs/DECISIONS.md`.

## How the dashboard works

`sou dashboard` reads every valid profile in `data/profiles/`, computes consensus codes, reliability and clusters, injects the result into `dashboard/template.html`, and writes `site/index.html` plus `site/data.json`. With no real profiles it falls back to random demo data and shows a banner saying so. The `dashboard` workflow runs this on every push to `main`, so committing new profiles updates the published atlas. `site/` is not committed.

The template is one self-contained HTML file in a retro terminal style (Courier New, a window frame with a title bar, an ASCII-art title and a working `sou:` command prompt) using Chart.js 4.4.1 from cdnjs. Views are Atlas (sortable heatmap), Profile (radar by perspective, codes by model and language, reasoning and evidence per dimension), Change over time, Typology, Reliability and Codebook. Keep the existing visual language when adding views.

## Layout

| Path | Contents |
| --- | --- |
| `codebook/codebook.yaml` | Single source of truth for dimensions; schema, docs and forms derive from it |
| `prompts/` | System, profile and open-coding prompts |
| `src/sense_of_us/` | `codebook.py`, `profile.py` (API calls), `analysis.py`, `dashboard.py`, `cli.py` |
| `dashboard/template.html` | Dashboard template |
| `data/countries/` | Unit lists (`pilot.csv`, `dynamics.csv`); ids sharing a prefix form a time series |
| `data/sources/<UNIT_ID>/` | Primary source packs |
| `data/profiles/` | One JSON file per model run, committed |
| `data/reports/` | Analysis outputs |
| `.github/workflows/` | Tests and dashboard deployment |

## Commands

`sou profile [--dry-run] [--ids ...]`, `sou analyse`, `sou dashboard [--demo]`, `sou compare-ratings`, `sou open-code`, `sou codebook-md`, `sou schema`, `sou rating-form`.

## Conventions

1. After any change to `codebook/codebook.yaml`, run `sou schema` and `sou codebook-md` and commit the regenerated files with it.
2. Never commit `.env`, API keys or files containing them.
3. Never invent sources, data or citations in docs, code comments or dashboard copy.
4. Prose uses British spelling, no em dashes, sentence case and plain direct sentences.
5. Every new function gets a test. Tests must run without an API key.
6. Profile JSON files are immutable once written. Re-runs go to new files or use `--overwrite` explicitly.
7. Model names live in `config.yaml`. Check docs.claude.com for current names before adding new ones.
8. Any new dashboard view must work with demo data, respect light and dark mode, and stay keyboard accessible.

## Task backlog

Work in order unless the user says otherwise. One branch per task, small commits, design choices logged in `docs/DECISIONS.md`.

| ID | Task | Acceptance criteria |
| --- | --- | --- |
| T1 | `sou profile --batch` using the Message Batches API, with submit, poll and collect steps | Same output files as the synchronous path; resumable if interrupted |
| T2 | `--mode narrative` restricting evidence to constitution, anthem, symbols and textbook sources, with `mode` stored in metadata | Narrative and full profiles distinguishable in `profiles_flat.csv`; dashboard ignores narrative-mode profiles except in the myth-gap view |
| T3 | `sou compare --ids X` writing a markdown table of codes across models, languages and perspectives with each dimension's reasoning | File in `data/reports/compare_<id>.md` |
| T4 | `--reveal-outcome "text"` flag that appends a known outcome to the prompt, stored in metadata | Analysis reports the shift per dimension between runs with and without it |
| T5 | Source-check helper listing every evidence item per profile with a column for the user to mark verified or fabricated | `data/reports/source_check.csv`; fabrication rate shown on the Reliability view |
| T6 | Human-agreement panel on the Reliability view, reading `data/reports/human_vs_model.csv` | Bars for human-only and human-plus-model alpha per dimension |
| T7 | `src/sense_of_us/external.py` loaders for user-downloaded Atlas complexity, V-Dem, fractionalisation and World Values Survey files, merged on ISO3 and year | `data/reports/merged.csv`; loaders tolerate missing files |
| T8 | Myth-gap calculation comparing narrative-mode codes with survey-based codes the user enters | Gap per unit and dimension, shown as a new column group in the Atlas view |
| T9 | Outcomes view plotting each hypothesis in `docs/FRAMEWORK.md` section 9, units labelled | New tab; empty state explains which data file is missing |
| T10 | Tag release `v0.5` with a changelog once the codebook is frozen | Release on GitHub |

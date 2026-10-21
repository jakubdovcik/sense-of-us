# Sense of Us

![tests](../../actions/workflows/tests.yml/badge.svg)

Tools and a research plan for measuring a society's **sense of us**, the concept developed by Ricardo Hausmann at the Harvard Growth Lab to explain why some societies achieve the coordination needed for state capacity and growth while others fragment.

The project codes countries against a codebook of nine dimensions (radius, boundary permeability, glue, myth arc, orientation, contestation, elite–mass bond, salience, nesting), tests how reliably AI models and human experts agree, builds a typology, studies how a sense of us arises, evolves, breaks down or is superseded, and links profiles to outcomes such as economic complexity. Results are published as the **Sense of Us atlas**, a dashboard on GitHub Pages that rebuilds whenever new profiles are committed.

## Start here

| Document | Purpose |
| --- | --- |
| [docs/FRAMEWORK.md](docs/FRAMEWORK.md) | The analytical framework, hypotheses and validity checks |
| [docs/RESEARCH_PLAN.md](docs/RESEARCH_PLAN.md) | Task checklist |
| [docs/CODEBOOK.md](docs/CODEBOOK.md) | Human-readable codebook (generated) |
| [docs/LITERATURE.md](docs/LITERATURE.md) | Sources and reading list |
| [CLAUDE.md](CLAUDE.md) | Instructions and task backlog for Claude Code |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
cp .env.example .env            # add your Anthropic API key
export $(cat .env | xargs)
sou profile --dry-run --ids CSK-1990 --runs 1   # no API calls
sou profile --ids CSK-1990 --runs 1 --models claude-sonnet-5-5 --languages English
sou analyse
sou dashboard          # writes site/index.html; demo data if no profiles yet
```

## Pipeline

1. `sou profile` sends each unit, period and evidence cut-off to Claude with the codebook and any source pack, and forces a structured answer that matches the schema derived from the codebook.
2. Profiles are saved one file per model, language, perspective and run.
3. `sou analyse` computes Krippendorff's alpha across runs, models and languages, builds consensus codes, clusters units into types and collects open features.
4. `sou compare-ratings` measures agreement between human experts and the model consensus.
5. `sou open-code` asks Claude to propose new codebook categories from everything the codebook missed.
6. `sou dashboard` builds the atlas. The `dashboard` workflow rebuilds and deploys it on every push to `main`.

## Status

Version 0.1. Scaffold, framework and dashboard ready; pilot not yet run, so the published atlas shows demo data.

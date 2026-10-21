"""Load the research design and the ethnography and culture readings, and render the design as Markdown."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .codebook import ROOT, load_codebook

FRAMEWORK_PATH = ROOT / "research" / "framework.yaml"
READINGS_DIR = ROOT / "research" / "readings"
LAYER_ORDER = ["narrative", "institutional", "behavioural", "lived"]
STANCES = ["supports", "complicates", "contradicts", "new"]


def load_framework(path: Path = FRAMEWORK_PATH) -> dict[str, Any]:
    """Read the research design and check its dimensions match the codebook."""
    with open(path, encoding="utf-8") as f:
        fw = yaml.safe_load(f)
    dim_ids = [d["id"] for d in load_codebook()["dimensions"]]
    missing = [d for d in dim_ids if d not in fw["dimensions"]]
    extra = [d for d in fw["dimensions"] if d not in dim_ids]
    if missing or extra:
        raise ValueError(f"framework dimensions differ from the codebook: missing {missing}, unknown {extra}")
    for d, spec in fw["dimensions"].items():
        if set(spec["layers"]) != set(LAYER_ORDER):
            raise ValueError(f"{d} must describe exactly these layers: {LAYER_ORDER}")
    return fw


def parse_reading(text: str, name: str = "") -> dict[str, Any]:
    """Split a reading into its YAML header and Markdown body, and check the stances."""
    if not text.startswith("---"):
        raise ValueError(f"{name}: a reading must start with a YAML header between --- lines")
    _, header, body = text.split("---", 2)
    meta = yaml.safe_load(header) or {}
    for key in ("title", "unit", "status", "summary"):
        if not meta.get(key):
            raise ValueError(f"{name}: missing {key}")
    dim_ids = {d["id"] for d in load_codebook()["dimensions"]}
    for dim, stance in (meta.get("dimensions") or {}).items():
        if dim not in dim_ids:
            raise ValueError(f"{name}: unknown dimension {dim}")
        if stance not in STANCES:
            raise ValueError(f"{name}: stance for {dim} must be one of {STANCES}")
    return {**meta, "file": name, "body": body.strip()}


def load_readings(folder: Path = READINGS_DIR) -> list[dict[str, Any]]:
    """Every reading in the folder except the template and README, sorted by unit and title."""
    if not folder.exists():
        return []
    readings = [parse_reading(p.read_text(encoding="utf-8"), p.name)
                for p in sorted(folder.glob("*.md")) if p.name not in {"TEMPLATE.md", "README.md"}]
    return sorted(readings, key=lambda r: (str(r["unit"]), str(r["title"])))


def contradiction_flags(readings: list[dict[str, Any]], threshold: int = 2) -> dict[str, list[str]]:
    """Unit and dimension pairs where at least `threshold` readings contradict the code."""
    counts: dict[tuple[str, str], int] = {}
    for r in readings:
        for dim, stance in (r.get("dimensions") or {}).items():
            if stance == "contradicts":
                counts[(r["unit"], dim)] = counts.get((r["unit"], dim), 0) + 1
    flags: dict[str, list[str]] = {}
    for (unit, dim), n in sorted(counts.items()):
        if n >= threshold:
            flags.setdefault(unit, []).append(dim)
    return flags


def render_framework_md(fw: dict[str, Any] | None = None) -> str:
    fw = fw or load_framework()
    names = {d["id"]: d["name"] for d in load_codebook()["dimensions"]}
    questions = {d["id"]: d["question"] for d in load_codebook()["dimensions"]}
    layers = {l["id"]: l["name"] for l in fw["layers"]}
    it = fw["interpretive"]
    out = [f"# {fw['title']} (v{fw['version']})", "",
           "Generated from `research/framework.yaml` by `sou framework-md`. Do not edit by hand.", "",
           fw["aim"], "", f"**Central question.** {fw['central_question']}", "", "## Two strands", ""]
    for s in fw["strands"]:
        out += [f"**{s['name']}.** {s['summary']} Produces: {s['produces']}.", ""]
    out += ["How the strands feed each other:", ""]
    out += [f"- {l['how']}" for l in fw["strand_links"]]
    out += ["", "## Research questions", "", "| | Question | How it is assessed | Data |", "| --- | --- | --- | --- |"]
    out += [f"| {q['id']} {q['name']} | {q['question']} | {q['assessed']} | {q['data']} |" for q in fw["research_questions"]]
    out += ["", "## Four layers of evidence", "", "| Layer | Shows | Method |", "| --- | --- | --- |"]
    out += [f"| {l['name']} | {l['shows']} | {l['method']} |" for l in fw["layers"]]
    out += ["", "## How assessment works", ""]
    out += [f"{i}. **{a['step']}.** {a['detail']}" for i, a in enumerate(fw["assessment"], 1)]
    out += ["", "## Questions by dimension", ""]
    for d, spec in fw["dimensions"].items():
        out += [f"### {names[d]}", "", f"*{questions[d]}*", "", "Questions to ask:", ""]
        out += [f"- {q}" for q in spec["questions"]]
        out += ["", "| Layer | What to look at | Where the data comes from |", "| --- | --- | --- |"]
        out += [f"| {layers[l]} | {spec['layers'][l]['look_at']} | {spec['layers'][l]['sources']} |" for l in LAYER_ORDER]
        out.append("")
    out += ["## Change over time", "", "| Question | Assessed as |", "| --- | --- |"]
    out += [f"| {c['question']} | {c['assessed']} |" for c in fw["change_questions"]]
    out += ["", f"Data: {fw['change_data']}.", "", "## Hypotheses", "", "| # | Hypothesis | Outcome measure | Data |", "| --- | --- | --- | --- |"]
    out += [f"| {h['id']} | {h['claim']} | {h['outcome']} | {h['data']} |" for h in fw["hypotheses"]]
    out += ["", "## Ethnography and culture strand", "", it["purpose"], "", "### What it is for", ""]
    out += [f"- **{r['name']}.** {r['detail']}" for r in it["roles"]]
    out += ["", "### Questions", ""]
    out += [f"{i}. {q}" for i, q in enumerate(it["questions"], 1)]
    out += ["", "### Materials", "", "| Material | Examples |", "| --- | --- |"]
    out += [f"| {m['name']} | {m['examples']} |" for m in it["materials"]]
    out += ["", "### Methods", "", "| Method | Use |", "| --- | --- |"]
    out += [f"| {m['name']} | {m['use']} |" for m in it["methods"]]
    out += ["", "### How readings are assessed", "", it["assessment"], "", "| Stance | Meaning |", "| --- | --- |"]
    out += [f"| {k} | {v} |" for k, v in it["stances"].items()]
    out += ["", "Quality criteria:", ""]
    out += [f"- {q}" for q in it["quality"]]
    out += ["", "### Reading template", "", "Copy `research/readings/TEMPLATE.md`. Each reading records:", ""]
    out += [f"- **{f['name']}.** {f['detail']}" for f in it["template_fields"]]
    out += ["", "### Starter studies", "", "| Study | Society | Idea | Materials |", "| --- | --- | --- | --- |"]
    out += [f"| {s['title']} | {s['unit']} | {s['idea']} | {s['materials']} |" for s in it["starter_studies"]]
    out += ["", "### Reading list", "", it["reading_list"]["note"], ""]
    out += [f"- {r}" for r in it["reading_list"]["items"]]
    out += ["", "## Data sources", "", f"Names only. Check links and access terms before use.", "",
            "| Source | Layer | Measures | Access |", "| --- | --- | --- | --- |"]
    out += [f"| {s['name']} | {layers[s['layer']]} | {s['measures']} | {s['access']} |" for s in fw["sources"]]
    return "\n".join(out) + "\n"

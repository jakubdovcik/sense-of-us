"""Generate sense-of-us profiles with Claude and save them as JSON."""
from __future__ import annotations

import csv
import json
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema

from .codebook import build_profile_schema, load_codebook, render_codebook_md
from .config import PROFILES_DIR, PROMPTS_DIR, SOURCES_DIR, load_config

TOOL_NAME = "record_profile"


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def load_units(csv_path: Path) -> list[dict[str, str]]:
    with open(csv_path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_sources(unit_id: str, max_chars: int) -> str:
    """Concatenate primary sources the researcher has collected for this unit."""
    folder = SOURCES_DIR / unit_id
    if not folder.exists():
        return ""
    parts, total = [], 0
    for p in sorted(folder.glob("*")):
        if p.suffix.lower() not in {".md", ".txt"}:
            continue
        text = p.read_text(encoding="utf-8")
        remaining = max_chars - total
        if remaining <= 0:
            break
        text = text[:remaining]
        parts.append(f'<document name="{p.name}">\n{text}\n</document>')
        total += len(text)
    return "\n\n".join(parts)


def build_prompt(unit: dict[str, str], perspective: str, language: str, max_source_chars: int) -> str:
    template = (PROMPTS_DIR / "profile.md").read_text(encoding="utf-8")
    if perspective == "national":
        perspective_text = "The society as a whole, recording rival narratives under contestation"
    else:
        perspective_text = (
            f"How the {perspective} group understands who 'we' are in {unit['unit']}. "
            "Code the 'us' as this group lives it, and note where it diverges from the official narrative."
        )
    if language == "English":
        language_text = "Draw mainly on English-language scholarship and sources."
    else:
        language_text = (
            f"Draw mainly on sources written in {language} (textbooks, speeches, press, scholarship), "
            f"as a well-read insider educated in {language} would."
        )
    sources = load_sources(unit["id"], max_source_chars)
    sources_block = (
        "Primary sources collected by the researcher. Prefer these and cite them by name.\n\n" + sources
        if sources
        else "No primary sources were supplied. Rely on your knowledge and say so in the evidence."
    )
    return template.format(
        unit=unit["unit"],
        period=unit["period"],
        cutoff=unit["cutoff"],
        perspective_text=perspective_text,
        language_text=language_text,
        sources_block=sources_block,
        codebook_md=render_codebook_md(),
    )


def _fake_from_schema(schema: dict[str, Any], rng: random.Random) -> Any:
    """Random but schema-valid output for dry runs and tests."""
    if "enum" in schema:
        return rng.choice(schema["enum"])
    t = schema.get("type")
    if t == "object":
        return {k: _fake_from_schema(v, rng) for k, v in schema.get("properties", {}).items()}
    if t == "array":
        n = max(schema.get("minItems", 0), 1)
        n = min(n, schema.get("maxItems", n))
        return [_fake_from_schema(schema["items"], rng) for _ in range(n)]
    if t == "integer":
        return rng.randint(0, 4)
    if t == "boolean":
        return rng.random() > 0.5
    if t == "string":
        return "dry run"
    return None


def call_claude(client: Any, model: str, system: str, prompt: str, schema: dict[str, Any], cfg: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    kwargs: dict[str, Any] = dict(
        model=model,
        max_tokens=cfg["max_tokens"],
        system=system,
        tools=[{
            "name": TOOL_NAME,
            "description": "Record one structured sense-of-us profile.",
            "input_schema": schema,
        }],
        tool_choice={"type": "tool", "name": TOOL_NAME},
        messages=[{"role": "user", "content": prompt}],
    )
    if cfg.get("temperature") is not None:
        kwargs["temperature"] = cfg["temperature"]
    resp = client.messages.create(**kwargs)
    block = next(b for b in resp.content if b.type == "tool_use")
    usage = {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}
    return block.input, usage


def run_profiles(
    units_csv: Path,
    unit_ids: list[str] | None = None,
    models: list[str] | None = None,
    runs: int | None = None,
    languages: list[str] | None = None,
    use_csv_perspectives: bool = False,
    dry_run: bool = False,
    overwrite: bool = False,
) -> list[Path]:
    cfg = load_config()
    schema = build_profile_schema(load_codebook())
    system = (PROMPTS_DIR / "system.md").read_text(encoding="utf-8")
    models = models or cfg["models"]
    runs = runs or cfg["runs_per_model"]
    languages = languages or cfg["languages"]

    client = None
    if not dry_run:
        import anthropic  # imported here so dry runs need no API key
        client = anthropic.Anthropic()

    units = load_units(units_csv)
    if unit_ids:
        units = [u for u in units if u["id"] in unit_ids]
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for unit in units:
        perspectives = unit["perspectives"].split(";") if use_csv_perspectives else ["national"]
        unit_langs = [unit["national_language"] if l == "national" else l for l in languages]
        unit_langs = list(dict.fromkeys(unit_langs))  # drop duplicates, e.g. English twice
        for model in models:
            for lang in unit_langs:
                for persp in perspectives:
                    for r in range(1, runs + 1):
                        name = f"{unit['id']}__{slug(model)}__{slug(lang)}__{slug(persp)}__r{r}.json"
                        path = PROFILES_DIR / name
                        if path.exists() and not overwrite:
                            continue
                        prompt = build_prompt(unit, persp, lang, cfg["max_source_chars"])
                        if dry_run:
                            rng = random.Random(name)
                            profile, usage = _fake_from_schema(schema, rng), {}
                        else:
                            profile, usage = _call_with_retry(client, model, system, prompt, schema, cfg)
                        errors = sorted(e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(profile))
                        record = {
                            "meta": {
                                "unit_id": unit["id"], "unit": unit["unit"], "period": unit["period"],
                                "cutoff": unit["cutoff"], "model": model, "language": lang,
                                "perspective": persp, "run": r, "dry_run": dry_run,
                                "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                "usage": usage, "schema_valid": not errors, "schema_errors": errors[:20],
                            },
                            "profile": profile,
                        }
                        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
                        written.append(path)
                        print(f"wrote {path.name}{'' if not errors else f' ({len(errors)} schema errors)'}")
    return written


def _call_with_retry(client: Any, model: str, system: str, prompt: str, schema: dict[str, Any], cfg: dict[str, Any], tries: int = 4):
    for attempt in range(tries):
        try:
            return call_claude(client, model, system, prompt, schema, cfg)
        except Exception as exc:  # rate limits and transient errors
            if attempt == tries - 1:
                raise
            wait = 2 ** attempt * 5
            print(f"  retrying in {wait}s after {type(exc).__name__}: {exc}")
            time.sleep(wait)

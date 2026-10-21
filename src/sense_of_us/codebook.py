"""Load the codebook and derive the JSON schema, docs and rating forms from it."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CODEBOOK_PATH = ROOT / "codebook" / "codebook.yaml"


def load_codebook(path: Path = CODEBOOK_PATH) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _evidence_schema(cb: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "array",
        "minItems": 1,
        "items": {
            "type": "object",
            "required": ["claim", "source_type", "source", "date"],
            "properties": {
                "claim": {"type": "string"},
                "source_type": {"type": "string", "enum": cb["evidence_types"]},
                "source": {"type": "string", "description": "Specific document, clause, speech or study"},
                "date": {"type": "string", "description": "Year or date of the source (YYYY or YYYY-MM-DD)"},
            },
        },
    }


def _value_schema(dim: dict[str, Any]) -> dict[str, Any]:
    t = dim["type"]
    if t == "ordinal":
        return {"type": "integer", "enum": [int(k) for k in dim["scale"].keys()]}
    if t == "multilabel":
        opts = list(dim["options"].keys())
        return {
            "type": "object",
            "required": ["primary", "secondary"],
            "properties": {
                "primary": {"type": "string", "enum": opts},
                "secondary": {
                    "type": "array",
                    "items": {"type": "string", "enum": opts},
                    "maxItems": dim.get("max_secondary", 3),
                },
            },
        }
    if t == "flags":
        return {
            "type": "object",
            "required": list(dim["options"].keys()),
            "properties": {k: {"type": "boolean"} for k in dim["options"]},
        }
    if t == "relations":
        return {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["level", "entity", "relation"],
                "properties": {
                    "level": {"type": "string", "enum": ["subnational", "supranational"]},
                    "entity": {"type": "string"},
                    "relation": {"type": "string", "enum": list(dim["relation_values"].keys())},
                },
            },
        }
    raise ValueError(f"Unknown dimension type: {t}")


def build_profile_schema(cb: dict[str, Any] | None = None) -> dict[str, Any]:
    """JSON schema for one profile. Used as the tool input schema for the model."""
    cb = cb or load_codebook()
    dim_props: dict[str, Any] = {}
    for dim in cb["dimensions"]:
        props: dict[str, Any] = {
            "value": _value_schema(dim),
            "confidence": {"type": "string", "enum": cb["confidence_levels"]},
            "reasoning": {"type": "string", "description": "Two to four sentences justifying the code"},
            "evidence": _evidence_schema(cb),
        }
        required = ["value", "confidence", "reasoning", "evidence"]
        for extra, desc in (dim.get("extra_fields") or {}).items():
            is_list = "(list)" in desc
            props[extra] = {"type": "array", "items": {"type": "string"}} if is_list else {"type": "string"}
            props[extra]["description"] = desc
            required.append(extra)
        dim_props[dim["id"]] = {"type": "object", "required": required, "properties": props}

    return {
        "type": "object",
        "required": ["unit", "period", "summary", "dimensions", "open_features", "typology_guess"],
        "properties": {
            "unit": {"type": "string"},
            "period": {"type": "string"},
            "summary": {"type": "string", "description": "150 to 250 word narrative of this society's sense of us"},
            "dimensions": {
                "type": "object",
                "required": [d["id"] for d in cb["dimensions"]],
                "properties": dim_props,
            },
            "open_features": {
                "type": "array",
                "description": "Unifying features or myths the codebook does not capture",
                "items": {
                    "type": "object",
                    "required": ["label", "description"],
                    "properties": {"label": {"type": "string"}, "description": {"type": "string"}},
                },
            },
            "typology_guess": {
                "type": "string",
                "enum": list(cb["hypothesised_types"].keys()) + ["none_fits"],
            },
        },
    }


def render_codebook_md(cb: dict[str, Any] | None = None) -> str:
    cb = cb or load_codebook()
    out = [f"# {cb['title']} (v{cb['version']})", "", "Generated from `codebook/codebook.yaml`. Do not edit by hand.", ""]
    for dim in cb["dimensions"]:
        out += [f"## {dim['name']} (`{dim['id']}`)", "", f"*{dim['question']}*", "", f"Type {dim['type']}.", ""]
        if "scale" in dim:
            out += ["| Code | Anchor |", "| --- | --- |"]
            out += [f"| {k} | {v} |" for k, v in dim["scale"].items()]
        if "options" in dim:
            out += ["| Option | Meaning |", "| --- | --- |"]
            out += [f"| `{k}` | {v} |" for k, v in dim["options"].items()]
        if "relation_values" in dim:
            out += ["| Relation | Meaning |", "| --- | --- |"]
            out += [f"| `{k}` | {v} |" for k, v in dim["relation_values"].items()]
        for extra, desc in (dim.get("extra_fields") or {}).items():
            out += ["", f"Extra field `{extra}`. {desc}."]
        out.append("")
    out += ["## Hypothesised types", "", "| Type | Profile |", "| --- | --- |"]
    out += [f"| `{k}` | {v} |" for k, v in cb["hypothesised_types"].items()]
    return "\n".join(out) + "\n"


def render_rating_form(unit: str, period: str, cb: dict[str, Any] | None = None) -> str:
    """Blank form for a human expert to code a country independently."""
    cb = cb or load_codebook()
    out = [
        f"# Expert rating form, {unit}, {period}",
        "",
        "Code each dimension from your own knowledge before reading any AI profile.",
        "Write one line of evidence for each code. Leave a field blank if unsure.",
        "",
        "Rater name ______  Relationship to the country ______  Date ______",
        "",
    ]
    for dim in cb["dimensions"]:
        out += [f"## {dim['name']}", "", dim["question"], ""]
        if "scale" in dim:
            out += [f"- [ ] {k} {v}" for k, v in dim["scale"].items()]
        elif "options" in dim:
            out += [f"- [ ] `{k}` {v}" for k, v in dim["options"].items()]
            if dim["type"] == "multilabel":
                out += ["", "Mark one primary (P) and up to three secondary (S)."]
        elif "relation_values" in dim:
            out += ["Sub-national identity ______ relation (nested / competing / absent) ______",
                    "Supranational identity ______ relation (nested / competing / absent) ______"]
        out += ["", "Confidence (low / medium / high) ______", "", "Evidence ______", ""]
    return "\n".join(out) + "\n"

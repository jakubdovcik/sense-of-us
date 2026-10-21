import json
import random

import jsonschema
import pandas as pd

from sense_of_us import analysis as A
from sense_of_us.codebook import build_profile_schema, render_codebook_md, render_rating_form
from sense_of_us.profile import _fake_from_schema, build_prompt, load_units
from sense_of_us.codebook import ROOT


def test_schema_accepts_fake_profile():
    schema = build_profile_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    fake = _fake_from_schema(schema, random.Random(1))
    jsonschema.validate(fake, schema)


def test_prompt_and_docs_render():
    unit = load_units(ROOT / "data/countries/pilot.csv")[0]
    prompt = build_prompt(unit, "Slovak", "Slovak", 1000)
    assert unit["unit"] in prompt and "Radius" in prompt
    assert "Radius" in render_codebook_md()
    assert "Expert rating form" in render_rating_form("Slovakia", "2015-2024")


def test_alpha_perfect_and_random():
    assert A.krippendorff_alpha([[1, 1], [3, 3], [4, 4]]) == 1.0
    assert A.krippendorff_alpha([["a", "a"], ["b", "b"]], "nominal") == 1.0
    assert A.krippendorff_alpha([[0, 4], [4, 0], [0, 4]]) < 0


def test_analysis_runs_on_fake_profiles(tmp_path):
    schema = build_profile_schema()
    for i, unit in enumerate(["AAA", "BBB", "CCC", "DDD"]):
        for model in ["m1", "m2"]:
            for r in (1, 2):
                rec = {"meta": {"unit_id": unit, "unit": unit, "period": "2000", "cutoff": "2000",
                                "model": model, "language": "English", "perspective": "national",
                                "run": r, "dry_run": False, "schema_valid": True},
                       "profile": _fake_from_schema(schema, random.Random(f"{unit}{model}{r}"))}
                (tmp_path / f"{unit}_{model}_{r}.json").write_text(json.dumps(rec))
    df = A.flatten(A.load_profiles(tmp_path))
    rel = A.reliability_report(df)
    assert set(rel["factor"]) == {"runs", "models", "languages"}
    cons = A.consensus(df)
    assert len(cons) == 4
    assigned, _ = A.typology(cons, k=2)
    assert assigned["cluster"].nunique() == 2


def test_dashboard_builds_with_demo_data(tmp_path):
    from sense_of_us.dashboard import PLACEHOLDER, build_site
    out = build_site(tmp_path, demo=True)
    html = out.read_text(encoding="utf-8")
    assert PLACEHOLDER not in html
    payload = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
    assert payload["meta"]["demo"] is True
    listed = {u["id"] for p in (ROOT / "data/countries").glob("*.csv") for u in load_units(p)}
    assert {u["id"] for u in payload["units"]} == listed
    assert all(set(payload["ordinal"]) <= set(u["consensus"]) for u in payload["units"])


def test_framework_matches_codebook_and_renders():
    from sense_of_us.codebook import load_codebook
    from sense_of_us.research import LAYER_ORDER, load_framework, render_framework_md
    fw = load_framework()
    assert list(fw["dimensions"]) == [d["id"] for d in load_codebook()["dimensions"]]
    assert all(set(s["layers"]) == set(LAYER_ORDER) for s in fw["dimensions"].values())
    assert {s["layer"] for s in fw["sources"]} <= set(LAYER_ORDER)
    md = render_framework_md(fw)
    assert "## Ethnography and culture strand" in md and "### Radius" in md


READING = """---
title: Test reading
unit: SVK-2015
status: proposed
summary: A short summary.
dimensions:
  radius: contradicts
  glue: new
---

## Observations

Text.
"""


def test_parse_reading_and_rejects_bad_stance():
    import pytest
    from sense_of_us.research import parse_reading
    r = parse_reading(READING, "x.md")
    assert r["dimensions"]["radius"] == "contradicts" and r["body"].startswith("## Observations")
    with pytest.raises(ValueError):
        parse_reading(READING.replace("contradicts", "maybe"), "x.md")
    with pytest.raises(ValueError):
        parse_reading("no header", "x.md")


def test_load_readings_skips_template_and_flags_contradictions(tmp_path):
    from sense_of_us.research import READINGS_DIR, contradiction_flags, load_readings
    (tmp_path / "TEMPLATE.md").write_text((READINGS_DIR / "TEMPLATE.md").read_text(encoding="utf-8"))
    (tmp_path / "a.md").write_text(READING)
    (tmp_path / "b.md").write_text(READING.replace("Test reading", "Second reading"))
    readings = load_readings(tmp_path)
    assert [r["title"] for r in readings] == ["Second reading", "Test reading"]
    assert contradiction_flags(readings) == {"SVK-2015": ["radius"]}
    assert contradiction_flags(readings[:1]) == {}
    assert load_readings(tmp_path / "missing") == []


def test_template_reading_is_valid():
    from sense_of_us.research import READINGS_DIR, parse_reading
    parse_reading((READINGS_DIR / "TEMPLATE.md").read_text(encoding="utf-8"), "TEMPLATE.md")

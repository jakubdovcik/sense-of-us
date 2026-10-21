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
    assert len(payload["units"]) >= 12
    assert all(set(payload["ordinal"]) <= set(u["consensus"]) for u in payload["units"])

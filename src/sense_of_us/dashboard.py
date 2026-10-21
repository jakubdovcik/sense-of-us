"""Build the static dashboard (site/index.html) from saved profiles."""
from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from . import analysis as A
from .codebook import ROOT, build_profile_schema, load_codebook
from .profile import _fake_from_schema, load_units

TEMPLATE = ROOT / "dashboard" / "template.html"
PLACEHOLDER = "/*__SOU_DATA__*/null"


def _family(unit_id: str) -> str:
    return unit_id.split("-")[0]


def demo_records(seed: int = 7) -> list[dict[str, Any]]:
    """Plausible-looking random profiles so the dashboard can be previewed before the pilot runs.

    Each unit gets a random base profile; runs, models and languages add small noise.
    The output is placeholder data, never findings.
    """
    cb = load_codebook()
    schema = build_profile_schema(cb)
    ords = A.ordinal_dims(cb)
    scales = {d["id"]: sorted(int(k) for k in d["scale"]) for d in cb["dimensions"] if d["type"] == "ordinal"}
    units = load_units(ROOT / "data/countries/pilot.csv") + load_units(ROOT / "data/countries/dynamics.csv")
    rng = random.Random(seed)
    records = []
    for u in units:
        base = _fake_from_schema(schema, random.Random(f"{seed}-{u['id']}"))
        base["summary"] = (
            f"Demo text for {u['unit']} ({u['period']}). Run `sou profile` and rebuild the dashboard "
            "to replace this with a real profile."
        )
        variants = [(m, l, "national", r) for m in ("model-a", "model-b") for l in ("English", u["national_language"]) for r in (1, 2)]
        variants += [("model-a", "English", p, 1) for p in u["perspectives"].split(";") if p != "national"]
        for model, lang, persp, run in variants:
            prof = json.loads(json.dumps(base))
            for d in ords:
                lo, hi = scales[d][0], scales[d][-1]
                shift = rng.choice([-1, 0, 0, 0, 1]) + (rng.choice([-2, -1, 1, 2]) if persp != "national" else 0)
                prof["dimensions"][d]["value"] = max(lo, min(hi, base["dimensions"][d]["value"] + shift))
            records.append({"meta": {"unit_id": u["id"], "unit": u["unit"], "period": u["period"], "cutoff": u["cutoff"],
                                     "model": model, "language": lang, "perspective": persp, "run": run,
                                     "dry_run": True, "schema_valid": True, "file": f"demo-{u['id']}-{model}-{lang}-{persp}-{run}"},
                            "profile": prof})
    return records


def build_payload(records: list[dict[str, Any]], demo: bool, k: int = 4) -> dict[str, Any]:
    cb = load_codebook()
    ords = A.ordinal_dims(cb)
    df = A.flatten(records)
    cons = A.consensus(df)
    rel = A.reliability_report(df)
    assigned, means = A.typology(cons, k) if len(cons) >= 3 else (pd.DataFrame(columns=["unit_id", "cluster"]), pd.DataFrame())
    clusters = dict(zip(assigned["unit_id"], assigned["cluster"].astype(int))) if len(assigned) else {}

    cutoffs = {r["meta"]["unit_id"]: r["meta"].get("cutoff", "") for r in records}
    units = []
    for _, row in cons.iterrows():
        uid = row["unit_id"]
        sub = df[df["unit_id"] == uid]
        nat = sub[sub["perspective"] == "national"]
        rep = next(r for r in records if r["meta"]["unit_id"] == uid and r["meta"]["perspective"] == "national")
        dims = rep["profile"]["dimensions"]
        detail = {}
        for d in cb["dimensions"]:
            entry = dims[d["id"]]
            detail[d["id"]] = {k: entry[k] for k in ("value", "confidence", "reasoning", "evidence")}
            for extra in (d.get("extra_fields") or {}):
                detail[d["id"]][extra] = entry.get(extra)
        units.append({
            "id": uid, "unit": row["unit"], "period": row["period"], "cutoff": cutoffs.get(uid, ""),
            "family": _family(uid), "cluster": clusters.get(uid),
            "consensus": {d: (None if pd.isna(row[d]) else float(row[d])) for d in ords},
            "glue_primary": row["glue_primary"],
            "glue_counts": nat["glue_primary"].value_counts().to_dict(),
            "myth": {c.replace("myth_arc_", ""): round(float(row[c]), 2) for c in cons.columns if c.startswith("myth_arc_")},
            "perspectives": {p: g[ords].median().round(2).to_dict() for p, g in sub.groupby("perspective")},
            "variants": [{"model": m, "language": l, **g[ords].mean().round(2).to_dict()}
                         for (m, l), g in nat.groupby(["model", "language"])],
            "typology_guess": nat["typology_guess"].mode().iloc[0] if len(nat) else None,
            "summary": rep["profile"]["summary"],
            "open_features": rep["profile"].get("open_features", []),
            "detail": detail,
            "n_profiles": int(len(sub)),
        })

    cluster_rows = []
    if len(means):
        for cid, r in means.iterrows():
            cluster_rows.append({"cluster": int(cid), "members": r["members"],
                                 "means": {d: float(r[d]) for d in ords if d in r}})

    return {
        "meta": {
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "demo": demo, "n_profiles": int(len(df)), "n_units": int(len(cons)),
            "models": sorted(df["model"].unique().tolist()), "languages": sorted(df["language"].unique().tolist()),
            "codebook_version": cb["version"],
        },
        "dims": [{"id": d["id"], "name": d["name"], "question": d["question"], "type": d["type"],
                  "scale": {str(k): v for k, v in (d.get("scale") or {}).items()},
                  "options": d.get("options") or d.get("relation_values") or {}} for d in cb["dimensions"]],
        "ordinal": ords,
        "types": cb["hypothesised_types"],
        "units": sorted(units, key=lambda u: (u["family"], u["period"])),
        "reliability": rel.where(pd.notna(rel), None).to_dict(orient="records"),
        "clusters": cluster_rows,
    }


def build_site(out_dir: Path, demo: bool = False, k: int = 4) -> Path:
    records = [] if demo else A.load_profiles()
    if not records:
        if not demo:
            print("No real profiles found, building with demo data.")
        records, demo = demo_records(), True
    payload = build_payload(records, demo, k)
    html = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in html:
        raise ValueError("Template is missing the data placeholder")
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "index.html"
    out.write_text(html.replace(PLACEHOLDER, data), encoding="utf-8")
    (out_dir / "data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out} ({'demo' if demo else 'real'} data, {payload['meta']['n_units']} units)")
    return out

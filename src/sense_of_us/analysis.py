"""Reliability, consensus, typology and open-coding analysis of saved profiles."""
from __future__ import annotations

import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .codebook import load_codebook
from .config import PROFILES_DIR, PROMPTS_DIR, REPORTS_DIR, load_config


def ordinal_dims(cb: dict[str, Any] | None = None) -> list[str]:
    cb = cb or load_codebook()
    return [d["id"] for d in cb["dimensions"] if d["type"] == "ordinal"]


def flag_options(cb: dict[str, Any] | None = None) -> dict[str, list[str]]:
    cb = cb or load_codebook()
    return {d["id"]: list(d["options"]) for d in cb["dimensions"] if d["type"] == "flags"}


def load_profiles(folder: Path = PROFILES_DIR, include_dry_run: bool = False) -> list[dict[str, Any]]:
    out = []
    for p in sorted(folder.glob("*.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        if rec["meta"].get("dry_run") and not include_dry_run:
            continue
        if not rec["meta"].get("schema_valid", True):
            continue
        rec["meta"]["file"] = p.name
        out.append(rec)
    return out


def flatten(records: Iterable[dict[str, Any]]) -> pd.DataFrame:
    cb = load_codebook()
    ords, flags = ordinal_dims(cb), flag_options(cb)
    rows = []
    for rec in records:
        m, dims = rec["meta"], rec["profile"]["dimensions"]
        row = {k: m[k] for k in ("unit_id", "unit", "period", "model", "language", "perspective", "run", "file")}
        for d in ords:
            row[d] = dims[d]["value"]
            row[f"{d}_conf"] = dims[d]["confidence"]
        row["glue_primary"] = dims["glue"]["value"]["primary"]
        row["glue_secondary"] = ";".join(dims["glue"]["value"]["secondary"])
        for dim_id, opts in flags.items():
            for o in opts:
                row[f"{dim_id}_{o}"] = int(bool(dims[dim_id]["value"].get(o)))
        row["typology_guess"] = rec["profile"].get("typology_guess")
        rows.append(row)
    return pd.DataFrame(rows)


def krippendorff_alpha(units: list[list[Any]], level: str = "interval") -> float:
    """Krippendorff's alpha. `units` is a list of the values coders gave each unit."""
    units = [[v for v in u if v is not None and not (isinstance(v, float) and np.isnan(v))] for u in units]
    units = [u for u in units if len(u) >= 2]
    if not units:
        return float("nan")

    def delta(a: Any, b: Any) -> float:
        return float((a - b) ** 2) if level == "interval" else float(a != b)

    n = sum(len(u) for u in units)
    d_o = sum(sum(delta(a, b) for a, b in itertools.permutations(u, 2)) / (len(u) - 1) for u in units) / n
    pooled = [v for u in units for v in u]
    d_e = sum(delta(a, b) for a, b in itertools.permutations(pooled, 2)) / (n * (n - 1))
    if d_e == 0:
        return 1.0
    return 1 - d_o / d_e


def reliability_report(df: pd.DataFrame) -> pd.DataFrame:
    """Agreement across runs, models and languages, holding everything else fixed.

    For models and languages, repeated runs are first collapsed (mean for ordinal
    codes, mode for glue) so the comparison isolates that one factor.
    """
    df = df[df["perspective"] == "national"].copy()
    ords = ordinal_dims()
    designs = {
        "runs": (["unit_id", "model", "language"], None),
        "models": (["unit_id", "language"], "model"),
        "languages": (["unit_id", "model"], "language"),
    }
    rows = []
    for factor, (keys, vary) in designs.items():
        if vary is None:
            data = df
        else:
            data = df.groupby(keys + [vary]).agg(
                {**{d: "mean" for d in ords}, "glue_primary": lambda s: s.mode().iloc[0]}
            ).reset_index()
        for d in ords + ["glue_primary"]:
            level = "nominal" if d == "glue_primary" else "interval"
            units = [g[d].tolist() for _, g in data.groupby(keys)]
            multi = [u for u in units if len(u) >= 2]
            spread = round(float(np.mean([np.ptp(u) for u in multi])), 2) if multi and level == "interval" else None
            rows.append({"factor": factor, "dimension": d, "level": level,
                         "alpha": round(krippendorff_alpha(units, level), 3),
                         "mean_range": spread, "n_units": len(multi)})
    return pd.DataFrame(rows)


def consensus(df: pd.DataFrame, perspective: str = "national") -> pd.DataFrame:
    """One row per unit. Median of ordinal codes, mode of glue, share of runs flagging each myth element."""
    sub = df[df["perspective"] == perspective]
    ords = ordinal_dims()
    flag_cols = [c for c in df.columns if c.startswith("myth_arc_")]
    agg = sub.groupby(["unit_id", "unit", "period"]).agg(
        {**{d: "median" for d in ords}, **{c: "mean" for c in flag_cols},
         "glue_primary": lambda s: s.mode().iloc[0], "file": "count"}
    ).rename(columns={"file": "n_profiles"}).reset_index()
    return agg


def compare_with_ratings(cons: pd.DataFrame, ratings_csv: Path) -> pd.DataFrame:
    """Alpha between human raters and the model consensus, per dimension.

    ratings_csv needs columns unit_id, rater, then any ordinal dimension ids and glue_primary.
    """
    ratings = pd.read_csv(ratings_csv)
    model = cons.assign(rater="model_consensus")
    both = pd.concat([ratings, model[ratings.columns.intersection(model.columns)]], ignore_index=True)
    rows = []
    for d in ordinal_dims() + ["glue_primary"]:
        if d not in ratings.columns:
            continue
        level = "nominal" if d == "glue_primary" else "interval"
        all_units = [g[d].dropna().tolist() for _, g in both.groupby("unit_id")]
        human_units = [g[d].dropna().tolist() for _, g in ratings.groupby("unit_id")]
        rows.append({"dimension": d, "alpha_humans_and_model": round(krippendorff_alpha(all_units, level), 3),
                     "alpha_humans_only": round(krippendorff_alpha(human_units, level), 3)})
    return pd.DataFrame(rows)


def typology(cons: pd.DataFrame, k: int = 4) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cluster units on their consensus profile. Returns assignments and cluster means."""
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.preprocessing import StandardScaler

    ords = ordinal_dims()
    glue = pd.get_dummies(cons["glue_primary"], prefix="glue").astype(float)
    flags = cons[[c for c in cons.columns if c.startswith("myth_arc_")]]
    X = pd.concat([cons[ords].astype(float), glue, flags], axis=1).fillna(0)
    k = max(2, min(k, len(X) - 1))
    labels = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(StandardScaler().fit_transform(X))
    assigned = cons[["unit_id", "unit", "period"]].assign(cluster=labels)
    means = pd.concat([X, pd.Series(labels, name="cluster")], axis=1).groupby("cluster").mean().round(2)
    means["members"] = assigned.groupby("cluster")["unit_id"].apply(lambda s: ", ".join(s))
    return assigned, means


def open_features(records: list[dict[str, Any]]) -> pd.DataFrame:
    rows = [{"unit_id": r["meta"]["unit_id"], "model": r["meta"]["model"],
             "label": f["label"].strip().lower(), "description": f["description"]}
            for r in records for f in r["profile"].get("open_features", [])]
    df = pd.DataFrame(rows, columns=["unit_id", "model", "label", "description"])
    if not df.empty:
        counts = Counter(df["label"])
        df["label_count"] = df["label"].map(counts)
        df = df.sort_values(["label_count", "label"], ascending=[False, True])
    return df


def run_open_coding(records: list[dict[str, Any]], model: str | None = None) -> str:
    """Ask Claude to propose new codebook categories from summaries and open features."""
    import anthropic

    cfg = load_config()
    seen, blocks = set(), []
    for r in records:
        key = r["meta"]["unit_id"]
        if key in seen or r["meta"]["perspective"] != "national":
            continue
        seen.add(key)
        feats = "; ".join(f"{f['label']}: {f['description']}" for f in r["profile"].get("open_features", []))
        blocks.append(f"## {r['meta']['unit']} ({r['meta']['period']})\n{r['profile']['summary']}\nOpen features: {feats}")
    prompt = (PROMPTS_DIR / "open_coding.md").read_text(encoding="utf-8").format(profiles_block="\n\n".join(blocks))
    resp = anthropic.Anthropic().messages.create(
        model=model or cfg["models"][0], max_tokens=cfg["max_tokens"],
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")


def save(df: pd.DataFrame, name: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / name
    df.to_csv(path, index=False)
    print(f"wrote {path.relative_to(REPORTS_DIR.parents[1])}")
    return path

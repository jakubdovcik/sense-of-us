"""Command-line entry point: `sou <command>`."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .codebook import ROOT, build_profile_schema, render_codebook_md, render_rating_form
from .config import REPORTS_DIR


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="sou", description="Sense of Us research pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("profile", help="Generate profiles with Claude")
    pr.add_argument("--units", default="data/countries/pilot.csv")
    pr.add_argument("--ids", nargs="*", help="Only these unit ids, e.g. CSK-1990 SVK-2015")
    pr.add_argument("--models", nargs="*")
    pr.add_argument("--runs", type=int)
    pr.add_argument("--languages", nargs="*", help="e.g. English national")
    pr.add_argument("--perspectives", choices=["national", "from-csv"], default="national")
    pr.add_argument("--dry-run", action="store_true", help="Random schema-valid output, no API calls")
    pr.add_argument("--overwrite", action="store_true")

    sub.add_parser("schema", help="Write the JSON schema to codebook/profile.schema.json")
    sub.add_parser("codebook-md", help="Write docs/CODEBOOK.md from the YAML codebook")
    sub.add_parser("framework-md", help="Write docs/RESEARCH_DESIGN.md from research/framework.yaml")

    rf = sub.add_parser("rating-form", help="Write blank expert rating forms")
    rf.add_argument("--units", default="data/countries/pilot.csv")

    an = sub.add_parser("analyse", help="Reliability, consensus, typology and open features")
    an.add_argument("--k", type=int, default=4, help="Number of clusters for the typology")
    an.add_argument("--include-dry-run", action="store_true")

    cr = sub.add_parser("compare-ratings", help="Compare human ratings with the model consensus")
    cr.add_argument("--ratings", default="data/ratings/ratings.csv")

    db = sub.add_parser("dashboard", help="Build the static dashboard in site/")
    db.add_argument("--demo", action="store_true", help="Use random demo data")
    db.add_argument("--out", default="site")
    db.add_argument("--k", type=int, default=4)

    oc = sub.add_parser("open-code", help="Ask Claude to propose new codebook categories")
    oc.add_argument("--model")

    a = p.parse_args(argv)

    if a.cmd == "profile":
        from .profile import run_profiles
        run_profiles(ROOT / a.units, a.ids, a.models, a.runs, a.languages,
                     a.perspectives == "from-csv", a.dry_run, a.overwrite)

    elif a.cmd == "schema":
        out = ROOT / "codebook" / "profile.schema.json"
        out.write_text(json.dumps(build_profile_schema(), indent=2), encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)}")

    elif a.cmd == "codebook-md":
        out = ROOT / "docs" / "CODEBOOK.md"
        out.write_text(render_codebook_md(), encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)}")

    elif a.cmd == "framework-md":
        from .research import render_framework_md
        out = ROOT / "docs" / "RESEARCH_DESIGN.md"
        out.write_text(render_framework_md(), encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)}")

    elif a.cmd == "rating-form":
        from .profile import load_units
        folder = ROOT / "validation" / "forms"
        folder.mkdir(parents=True, exist_ok=True)
        for u in load_units(ROOT / a.units):
            (folder / f"{u['id']}.md").write_text(render_rating_form(u["unit"], u["period"]), encoding="utf-8")
        print(f"wrote forms to {folder.relative_to(ROOT)}")

    elif a.cmd == "analyse":
        from . import analysis as A
        recs = A.load_profiles(include_dry_run=a.include_dry_run)
        if not recs:
            print("No valid profiles found. Run `sou profile` first.")
            return
        df = A.flatten(recs)
        A.save(df, "profiles_flat.csv")
        A.save(A.reliability_report(df), "reliability.csv")
        cons = A.consensus(df)
        A.save(cons, "consensus.csv")
        if len(cons) >= 3:
            assigned, means = A.typology(cons, a.k)
            A.save(assigned, "typology_assignments.csv")
            A.save(means.reset_index(), "typology_clusters.csv")
        A.save(A.open_features(recs), "open_features.csv")

    elif a.cmd == "compare-ratings":
        from . import analysis as A
        cons = A.consensus(A.flatten(A.load_profiles()))
        A.save(A.compare_with_ratings(cons, ROOT / a.ratings), "human_vs_model.csv")

    elif a.cmd == "dashboard":
        from .dashboard import build_site
        build_site(ROOT / a.out, a.demo, a.k)

    elif a.cmd == "open-code":
        from . import analysis as A
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        out = REPORTS_DIR / "open_coding.md"
        out.write_text(A.run_open_coding(A.load_profiles(), a.model), encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

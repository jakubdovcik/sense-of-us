"""Load pipeline settings from config.yaml."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .codebook import ROOT

CONFIG_PATH = ROOT / "config.yaml"
DATA = ROOT / "data"
PROFILES_DIR = DATA / "profiles"
REPORTS_DIR = DATA / "reports"
SOURCES_DIR = DATA / "sources"
PROMPTS_DIR = ROOT / "prompts"


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

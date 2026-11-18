"""Settings for the lab. Reads ./.env first, then falls back to ../backend/.env for the API key
so we never have to copy secrets around."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

ROOT = Path(__file__).resolve().parent.parent
LOCALES = ROOT / "locales"
DATA = ROOT / "data"
CACHE = DATA / "cache"
OUT = ROOT / "out"
PROMPTS = Path(__file__).resolve().parent / "prompts"

load_dotenv(ROOT / ".env")
if not os.getenv("ANTHROPIC_API_KEY"):
    backend_env = ROOT.parent / "backend" / ".env"
    if backend_env.exists():
        key = dotenv_values(backend_env).get("ANTHROPIC_API_KEY")
        if key:
            os.environ["ANTHROPIC_API_KEY"] = key

SUPPORTED = ("lt", "lv", "et")
LANG_NAMES = {"lt": "Lithuanian", "lv": "Latvian", "et": "Estonian", "en": "English"}


@dataclass(frozen=True)
class Settings:
    gen_model: str = field(default_factory=lambda: os.getenv("BBL_GEN_MODEL", "claude-opus-5-5"))
    judge_model: str = field(default_factory=lambda: os.getenv("BBL_JUDGE_MODEL", "claude-opus-5-5"))
    # The "today" baseline: English generation + literal translation, run on the backend's model.
    baseline_model: str = field(default_factory=lambda: os.getenv("BBL_BASELINE_MODEL", "claude-sonnet-5-5"))
    xjudge_model: str = field(default_factory=lambda: os.getenv("BBL_XJUDGE_MODEL", ""))
    native_ear_model: str = field(default_factory=lambda: os.getenv("BBL_NATIVE_EAR_MODEL", "gemini-3.6-flash|gemini-3.5-flash-lite"))
    gen_effort: str = field(default_factory=lambda: os.getenv("BBL_GEN_EFFORT", "medium"))
    judge_effort: str = field(default_factory=lambda: os.getenv("BBL_JUDGE_EFFORT", "high"))
    max_repairs: int = field(default_factory=lambda: int(os.getenv("BBL_MAX_REPAIRS", "2")))
    use_fallbacks: bool = field(default_factory=lambda: os.getenv("BBL_FALLBACKS", "1") == "1")
    wikidata_ua: str = "bbl-research/0.1"


settings = Settings()

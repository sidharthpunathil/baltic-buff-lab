"""Thin wrapper over the Anthropic SDK: one structured-output call with usage accounting."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TypeVar

import anthropic
from pydantic import BaseModel

from .config import settings

T = TypeVar("T", bound=BaseModel)

_client: anthropic.Anthropic | None = None


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(max_retries=3)
    return _client


@dataclass
class Usage:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    seconds: float = 0.0
    by_step: dict[str, int] = field(default_factory=dict)

    def add(self, step: str, resp, dt: float) -> None:
        self.calls += 1
        self.input_tokens += resp.usage.input_tokens or 0
        self.output_tokens += resp.usage.output_tokens or 0
        self.cache_write_tokens += getattr(resp.usage, "cache_creation_input_tokens", 0) or 0
        self.cache_read_tokens += getattr(resp.usage, "cache_read_input_tokens", 0) or 0
        self.seconds += dt
        self.by_step[step] = self.by_step.get(step, 0) + 1


USAGE = Usage()


class LLMRefusal(RuntimeError):
    pass


def structured(
    *,
    step: str,
    model: str,
    system: str,
    user: str,
    schema: type[T],
    effort: str = "medium",
    max_tokens: int = 16000,
) -> T:
    """Call the model and return a validated pydantic object. `gemini-*` models route to Google
    (used as a cross-family judge / generator: WMT25 found model rank differs per language)."""
    if "|" in model:  # fallback chain, e.g. "gemini-3.6-flash|gemini-3.5-flash-lite"
        last: Exception | None = None
        for m in model.split("|"):
            try:
                return structured(step=step, model=m, system=system, user=user, schema=schema,
                                  effort=effort, max_tokens=max_tokens)
            except Exception as exc:
                last = exc
        raise RuntimeError(f"{step}: every model in chain failed: {last}")
    if model.startswith("gemini"):
        return _gemini(step=step, model=model, system=system, user=user, schema=schema)
    kwargs: dict = {}
    if settings.use_fallbacks:
        # Server-side refusal fallback (beta); harmless for sports copy, avoids a dead request.
        kwargs["extra_headers"] = {"anthropic-beta": "server-side-fallback-2026-07-01"}
        kwargs["extra_body"] = {"fallbacks": "default"}
    t0 = time.monotonic()
    resp = client().messages.parse(
        model=model,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
        output_format=schema,
        output_config={"effort": effort},
        **kwargs,
    )
    USAGE.add(step, resp, time.monotonic() - t0)
    if resp.stop_reason == "refusal":
        raise LLMRefusal(f"{step}: model declined ({getattr(resp, 'stop_details', None)})")
    if resp.parsed_output is None:
        raise RuntimeError(f"{step}: no parsed output (stop_reason={resp.stop_reason})")
    return resp.parsed_output


_gclient = None


def _gemini(*, step: str, model: str, system: str, user: str, schema: type[T]) -> T:
    import os

    from dotenv import dotenv_values
    from google import genai
    from google.genai import types

    from .config import ROOT

    global _gclient
    if _gclient is None:
        acn = os.getenv("ACN_TOKEN")
        if acn:
            # Pooled-key proxy: rotates Gemini keys on 429/quota, which sank the first run's 2nd judge.
            _gclient = genai.Client(
                api_key="via-proxy",
                http_options=types.HttpOptions(
                    timeout=120_000,
                    api_version="v1beta",
                    base_url=os.getenv("BBL_GEMINI_BASE_URL", "https://key.sidharth.co/proxy/gemini"),
                    headers={"Authorization": f"Bearer {acn}"},
                ),
            )
        else:
            key = os.getenv("GEMINI_API_KEY") or dotenv_values(ROOT.parent / "backend" / ".env").get("GEMINI_API_KEY")
            _gclient = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=90_000, api_version="v1beta"))
    t0 = time.monotonic()
    last: Exception | None = None
    for attempt in range(2):
        try:
            resp = _gclient.models.generate_content(
                model=model,
                contents=user,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
            break
        except Exception as exc:  # transient 429/503s are common on Gemini
            last = exc
            time.sleep(5 * (attempt + 1))
    else:
        raise RuntimeError(f"{step}: gemini failed: {last}")
    dt = time.monotonic() - t0
    USAGE.calls += 1
    USAGE.seconds += dt
    um = resp.usage_metadata
    USAGE.input_tokens += (um.prompt_token_count or 0) if um else 0
    USAGE.output_tokens += (um.candidates_token_count or 0) if um else 0
    USAGE.by_step[step] = USAGE.by_step.get(step, 0) + 1
    if resp.parsed is not None:
        return resp.parsed if isinstance(resp.parsed, schema) else schema.model_validate(resp.parsed)
    return schema.model_validate_json(resp.text)

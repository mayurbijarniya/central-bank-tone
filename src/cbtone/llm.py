"""Label sentences hawkish, dovish or neutral with a language model.

Any OpenAI-compatible chat endpoint works (OpenRouter, Subconscious and others).
The endpoint, key and model come from `.env` or the environment:

    LLM_BASE_URL=https://openrouter.ai/api/v1
    LLM_API_KEY=...
    LLM_MODEL=...

The key is only ever sent in the request header; it is never logged or saved.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from cbtone import paths

LABELS = ("dovish", "hawkish", "neutral")

# The definitions follow the annotation guide of Shah, Paturi and Chava (2023),
# written for any central bank rather than the Federal Reserve only.
INSTRUCTIONS = """You classify sentences from central bank speeches by their monetary policy stance.

hawkish: points towards tighter monetary policy or higher interest rates. Examples: inflation
is too high or rising, prices or wages are accelerating, the economy is overheating, demand is
too strong, rates should rise or stay high, policy accommodation should be removed.

dovish: points towards easier monetary policy or lower interest rates. Examples: growth is weak
or slowing, unemployment is high or rising, inflation is low or falling below target, downside
risks, rates should fall or stay low, more stimulus or support is needed.

neutral: neither, including sentences that discuss other topics (payments, supervision,
history, procedures) or balance the two sides equally.

Descriptions of the economy carry a stance even without a policy statement: strong growth, a
tight labor market, rising employment or rising prices are hawkish; weak growth, slack, job
losses, falling prices or financial stress are dovish. Use neutral only when the sentence leans
neither way.

Judge the sentence on its own, from the speaker's point of view. Reply with JSON only:
{"labels": ["hawkish", "neutral", ...]}, one label per numbered sentence, in order."""


def settings() -> dict[str, str]:
    """Endpoint, key and model from the environment, falling back to the project's `.env`."""
    values = {}
    env_file = paths.ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")
    for key in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        if os.environ.get(key):
            values[key] = os.environ[key]
    missing = [k for k in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL") if not values.get(k)]
    if missing:
        raise RuntimeError(f"missing {', '.join(missing)} in .env or the environment")
    return values


@dataclass
class Usage:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    seconds: float = 0.0
    failures: list[str] = field(default_factory=list)


def prompt(sentences: list[str]) -> str:
    numbered = "\n".join(f"{i}. {s}" for i, s in enumerate(sentences, start=1))
    return f"Classify these {len(sentences)} sentences.\n\n{numbered}"


def parse(reply: str, expected: int) -> list[str] | None:
    """The labels in a reply, or None if it does not hold exactly one valid label per sentence."""
    match = re.search(r"\{.*\}", reply, re.DOTALL)
    if not match:
        return None
    try:
        labels = json.loads(match.group(0)).get("labels")
    except (json.JSONDecodeError, AttributeError):
        return None
    if not isinstance(labels, list) or len(labels) != expected:
        return None
    labels = [str(label).strip().lower() for label in labels]
    return labels if all(label in LABELS for label in labels) else None


def complete(messages: list[dict], config: dict[str, str], usage: Usage,
             timeout: float = 300) -> str:
    body = json.dumps(
        {"model": config["LLM_MODEL"], "messages": messages, "temperature": 0}
    ).encode()
    request = urllib.request.Request(
        config["LLM_BASE_URL"].rstrip("/") + "/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {config['LLM_API_KEY']}",
            "Content-Type": "application/json",
        },
    )
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    usage.seconds += time.monotonic() - started
    usage.calls += 1
    tokens = payload.get("usage") or {}
    usage.prompt_tokens += tokens.get("prompt_tokens", 0)
    usage.completion_tokens += tokens.get("completion_tokens", 0)
    return payload["choices"][0]["message"]["content"] or ""


def label(sentences: list[str], usage: Usage, config: dict[str, str] | None = None,
          attempts: int = 3) -> list[str | None]:
    """One label per sentence; None where the model's reply could not be read."""
    config = config or settings()
    messages = [
        {"role": "system", "content": INSTRUCTIONS},
        {"role": "user", "content": prompt(sentences)},
    ]
    for attempt in range(attempts):
        try:
            labels = parse(complete(messages, config, usage), len(sentences))
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as error:
            usage.failures.append(type(error).__name__)
            labels = None
        if labels is not None:
            return labels
        time.sleep(2 * (attempt + 1))
    return [None] * len(sentences)

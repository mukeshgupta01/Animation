"""Deterministic, child-friendly Tiny Tales narration profiles."""

from __future__ import annotations

import hashlib
import os
from typing import Any


VOICE_PROFILES: dict[str, dict[str, str]] = {
    "ana-us": {
        "voice": "en-US-AnaNeural",
        "rate": "-4%",
        "pitch": "+10Hz",
        "description": "cute US cartoon/conversation delivery",
    },
    "maisie-uk": {
        "voice": "en-GB-MaisieNeural",
        "rate": "-5%",
        "pitch": "+6Hz",
        "description": "friendly UK child-like delivery",
    },
    "natasha-au": {
        "voice": "en-AU-NatashaNeural",
        "rate": "-6%",
        "pitch": "+2Hz",
        "description": "friendly Australian delivery",
    },
    "ryan-uk": {
        "voice": "en-GB-RyanNeural",
        "rate": "-6%",
        "pitch": "+1Hz",
        "description": "friendly UK male delivery",
    },
}

DEFAULT_PROFILE = "ana-us"


def profile_names() -> tuple[str, ...]:
    return tuple(VOICE_PROFILES)


def select_voice_profile(
    profile_name: str | None = None,
    seed: str | None = None,
) -> dict[str, Any]:
    """Return a reproducible profile, preferring an explicit manifest choice."""
    requested = profile_name or os.environ.get("TINY_TALES_VOICE_PROFILE")
    if requested:
        if requested not in VOICE_PROFILES:
            raise ValueError(
                f"Unknown Tiny Tales voice profile {requested!r}; "
                f"choose one of {', '.join(profile_names())}"
            )
        selected = requested
    else:
        stable_seed = seed or os.environ.get("TINY_TALES_VOICE_SEED")
        if stable_seed:
            digest = hashlib.sha256(stable_seed.encode("utf-8")).digest()
            selected = profile_names()[int.from_bytes(digest[:4], "big") % len(VOICE_PROFILES)]
        else:
            # Preserve legacy/manual producer behaviour unless the runner or a
            # new producer supplies a stable ID or explicit profile.
            selected = DEFAULT_PROFILE
    return {"name": selected, **VOICE_PROFILES[selected]}

"""Opt-in, anonymous usage ping. OFF by default.

Enabled only when TOKENREEL_TELEMETRY=1 AND TOKENREEL_TELEMETRY_URL is set.
Sends no text, paths, hostnames, IPs we control, or identifiers. See TELEMETRY.md.
"""
from __future__ import annotations

import json
import os
import platform
import urllib.request

from . import __version__


def payload() -> dict:
    return {
        "v": __version__,
        "os": platform.system(),
        "py": platform.python_version().rsplit(".", 1)[0],
    }


def enabled() -> bool:
    return os.environ.get("TOKENREEL_TELEMETRY") == "1" and bool(os.environ.get("TOKENREEL_TELEMETRY_URL"))


def ping() -> bool:
    if not enabled() or os.environ.get("DO_NOT_TRACK") == "1":
        return False
    url = os.environ["TOKENREEL_TELEMETRY_URL"]
    if not url.startswith("https://"):
        return False
    req = urllib.request.Request(url, json.dumps(payload()).encode(), {"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=3).close()
        return True
    except Exception:  # noqa: BLE001 - telemetry must never break the tool
        return False

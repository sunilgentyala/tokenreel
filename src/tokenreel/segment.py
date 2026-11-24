"""Scene planning: split text into scenes and tag each with a visual kind.

Pure stdlib so the core installs with zero dependencies. spaCy is an optional
upgrade for better sentence and entity handling (extra: nlp).
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

_FENCE = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{2,}")
_STOP = frozenset(
    ["the", "and", "for", "with", "that", "this", "from", "are", "was", "were", "has", "have", "had", "not", "but", "you", "your", "can", "will", "into", "over", "then", "than", "its", "it's", "their", "there", "which", "when", "what", "how", "why"]
)
_MATH = re.compile(r"[=^∑∫√]|\\frac|\b\d+\s*[*/+\-]\s*\d+")
_FLOW = re.compile(r"\b(then|next|after that|finally|first|second|step \d+)\b", re.IGNORECASE)


@dataclass
class Scene:
    kind: str  # "code" | "math" | "flow" | "text"
    text: str
    keywords: list[str] = field(default_factory=list)
    lang: str = ""
    steps: list[str] = field(default_factory=list)


def keywords(text: str, k: int = 4) -> list[str]:
    counts = Counter(w.lower() for w in _WORD.findall(text) if w.lower() not in _STOP)
    return [w for w, _ in counts.most_common(k)]


def _kind(sentence: str) -> str:
    if _MATH.search(sentence):
        return "math"
    if _FLOW.search(sentence):
        return "flow"
    return "text"


def plan(text: str, max_chars: int = 220) -> list[Scene]:
    """Split text into scenes. Fenced code blocks become code scenes."""
    scenes: list[Scene] = []
    pos = 0
    for m in _FENCE.finditer(text):
        scenes += _prose(text[pos : m.start()], max_chars)
        scenes.append(Scene("code", m.group(2).rstrip(), keywords(m.group(2)), m.group(1)))
        pos = m.end()
    scenes += _prose(text[pos:], max_chars)
    return scenes


def _make(kind: str, text: str) -> Scene:
    return Scene(kind, text, keywords(text), steps=steps(text) if kind == "flow" else [])


def _prose(chunk: str, max_chars: int) -> list[Scene]:
    """Group consecutive sentences of the same kind, capped at max_chars."""
    out: list[Scene] = []
    buf, kind = "", ""
    for s in (x.strip() for x in _SENT.split(" ".join(chunk.split()))):
        if not s:
            continue
        k = _kind(s)
        if buf and (k != kind or len(buf) + len(s) + 1 > max_chars):
            out.append(_make(kind, buf))
            buf = ""
        buf = f"{buf} {s}".strip()
        kind = k
    if buf:
        out.append(_make(kind, buf))
    return out


_LEAD = re.compile(r"^(first(ly)?|second(ly)?|third(ly)?|then|next|after that|finally|lastly|step \d+)[,:]?\s+", re.IGNORECASE)


def steps(text: str, max_steps: int = 5) -> list[str]:
    """Split a flow scene into short step labels, dropping leading connectors."""
    out = []
    for sent in _SENT.split(text):
        sent = _LEAD.sub("", sent.strip()).rstrip(".!?")
        if sent:
            out.append(sent[0].upper() + sent[1:])
    return out[:max_steps]


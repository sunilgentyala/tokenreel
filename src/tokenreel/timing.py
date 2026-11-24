"""Word timings and captions.

A TTS or aligner backend supplies real word timings as a list of (word, start, end).
Without one, estimate_timings() spreads time over words by character weight so the
pipeline still works offline with no audio (silent preview renders).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

CHARS_PER_SEC = 15.0  # roughly 180 wpm


@dataclass
class Word:
    text: str
    start: float
    end: float


def spoken_form(text: str) -> str:
    """Make text alignable: aligners give no timing to bare digits and symbols."""
    reps = {"=": " equals ", "+": " plus ", "/": " over ", "^": " to the power of ", "%": " percent "}
    for k, v in reps.items():
        text = text.replace(k, v)
    ones = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    text = re.sub(r"\d", lambda m: f" {ones[int(m.group())]} ", text)
    return " ".join(text.split())


def estimate_timings(text: str, offset: float = 0.0, cps: float = CHARS_PER_SEC) -> list[Word]:
    words = spoken_form(text).split()
    t = offset
    out: list[Word] = []
    for w in words:
        d = max(0.18, (len(w) + 1) / cps)
        out.append(Word(w, round(t, 3), round(t + d, 3)))
        t += d
    return out


def _ts(x: float) -> str:
    ms = round(x * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def to_srt(words: list[Word], per_cue: int = 4) -> str:
    cues = []
    for n, i in enumerate(range(0, len(words), per_cue), 1):
        chunk = words[i : i + per_cue]
        cues.append(f"{n}\n{_ts(chunk[0].start)} --> {_ts(chunk[-1].end)}\n{' '.join(w.text for w in chunk)}\n")
    return "\n".join(cues)

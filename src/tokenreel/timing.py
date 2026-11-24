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


def _ass_ts(x: float) -> str:
    cs = round(x * 100)
    h, cs = divmod(cs, 360_000)
    m, cs = divmod(cs, 6_000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"


_ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Karaoke,{font},{size},{done},{todo},&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,5,0,2,80,80,{margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def to_ass(
    words: list[Word],
    per_cue: int = 4,
    font: str = "Segoe UI",
    size: int = 64,
    margin_v: int = 400,
    done: str = "&H0024BFFB",
    todo: str = "&H00FFFFFF",
) -> str:
    """Karaoke captions: each word fills with the `done` colour (ASS is BGR, default amber)
    exactly while it is spoken. Positions are real pixels on a 1080x1920 canvas."""
    out = [_ASS_HEAD.format(font=font, size=size, margin=margin_v, done=done, todo=todo)]
    for i in range(0, len(words), per_cue):
        chunk = words[i : i + per_cue]
        start = chunk[0].start
        parts = []
        for k, w in enumerate(chunk):
            nxt = chunk[k + 1].start if k + 1 < len(chunk) else w.end
            # centiseconds from cumulative rounding so a cue never drifts from its end time
            cs = round((nxt - start) * 100) - round((w.start - start) * 100)
            clean = w.text.replace("\\", "").replace("{", "").replace("}", "")
            parts.append("{\\kf" + str(max(1, cs)) + "}" + clean)
        text = " ".join(parts)
        out.append(f"Dialogue: 0,{_ass_ts(start)},{_ass_ts(chunk[-1].end)},Karaoke,,0,0,0,,{text}\n")
    return "".join(out)


def to_srt(words: list[Word], per_cue: int = 4) -> str:
    cues = []
    for n, i in enumerate(range(0, len(words), per_cue), 1):
        chunk = words[i : i + per_cue]
        cues.append(f"{n}\n{_ts(chunk[0].start)} --> {_ts(chunk[-1].end)}\n{' '.join(w.text for w in chunk)}\n")
    return "\n".join(cues)

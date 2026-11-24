"""Local, offline TTS through kokoro-onnx (extra: tts). No text leaves the machine.

kokoro-onnx on PyPI (0.4.7 at time of writing) returns audio only, no word timings, so
timings are calibrated: the estimated word weights are scaled to the true clip length.
That keeps captions in step with the audio per scene. For exact word times, run a forced
aligner (WhisperX, extra: align) on the wav and pass its words to to_srt().

Model files (about 350 MB) are downloaded by the user, never fetched silently:
  kokoro-v1.0.onnx and voices-v1.0.bin from the kokoro-onnx model-files-v1.0 release.
"""
from __future__ import annotations

import os
from pathlib import Path

from .timing import Word, estimate_timings

MODEL_DIR = Path(os.environ.get("TOKENREEL_MODELS", Path.home() / ".tokenreel" / "models"))
_engine = None


def available() -> bool:
    return (MODEL_DIR / "kokoro-v1.0.onnx").exists() and (MODEL_DIR / "voices-v1.0.bin").exists()


def _kokoro():
    global _engine
    if _engine is None:
        from kokoro_onnx import Kokoro  # lazy: optional dependency

        _engine = Kokoro(str(MODEL_DIR / "kokoro-v1.0.onnx"), str(MODEL_DIR / "voices-v1.0.bin"))
    return _engine


def synth(spoken_text: str, out_wav: Path, voice: str = "af_heart", speed: float = 1.0) -> float:
    """Write a wav, return its duration in seconds."""
    import soundfile as sf

    samples, rate = _kokoro().create(spoken_text, voice=voice, speed=speed, lang="en-us")
    sf.write(str(out_wav), samples, rate)
    return len(samples) / rate


def calibrated_words(spoken_text: str, duration: float, offset: float = 0.0) -> list[Word]:
    words = estimate_timings(spoken_text)
    if not words:
        return []
    scale = duration / words[-1].end
    return [Word(w.text, round(offset + w.start * scale, 3), round(offset + w.end * scale, 3)) for w in words]

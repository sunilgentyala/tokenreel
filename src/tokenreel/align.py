"""Exact word timings from audio via faster-whisper (extra: align). MIT, CPU friendly.

This replaces the calibrated estimate in tts.py when available. The aligner runs locally;
the small English model (about 75 MB) is downloaded once from the Hugging Face hub on first
use, then cached. Set TOKENREEL_WHISPER_MODEL to change the model size.

The script words are the source of truth for caption text. If the recognizer returns the
same number of words, script words get the recognizer's times. Otherwise the recognizer's
words are used as-is.
"""
from __future__ import annotations

import os
from pathlib import Path

from .timing import Word

_model = None


def _whisper():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel  # lazy: optional dependency

        _model = WhisperModel(os.environ.get("TOKENREEL_WHISPER_MODEL", "tiny.en"), device="cpu", compute_type="int8")
    return _model


def align(wav: Path, script_words: list[str], offset: float = 0.0) -> list[Word]:
    import numpy as np
    import soundfile as sf

    # decode our own wav and resample to 16 kHz mono, so faster-whisper never touches PyAV
    # (PyAV 19 broke its decode path)
    audio, rate = sf.read(str(wav), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if rate != 16000:
        n = int(len(audio) * 16000 / rate)
        audio = np.interp(np.linspace(0, len(audio) - 1, n), np.arange(len(audio)), audio).astype("float32")
    segments, _ = _whisper().transcribe(audio, word_timestamps=True, language="en", beam_size=1)
    heard = [w for seg in segments for w in (seg.words or [])]
    if not heard:
        return []
    if len(heard) == len(script_words):
        return [Word(t, round(offset + h.start, 3), round(offset + h.end, 3)) for t, h in zip(script_words, heard)]
    return [Word(h.word.strip(), round(offset + h.start, 3), round(offset + h.end, 3)) for h in heard]

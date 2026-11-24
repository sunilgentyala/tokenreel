"""TokenReel as an MCP server (extra: mcp). Runs over stdio by default.

Tools let an AI agent plan scenes from text, get estimated captions, and render a
narrated, captioned 1080x1920 video, all locally.

Security: the client never supplies file paths. Output goes to TOKENREEL_OUT (default
~/tokenreel-output), one fresh subfolder per render, and the file name is restricted to a
short allow-listed charset. Input size and scene count are capped. Everything runs offline.
"""
from __future__ import annotations

import os
import re
import shutil
import uuid
from dataclasses import asdict
from pathlib import Path

try:  # mcp 2.x
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

from .segment import plan
from .timing import estimate_timings, to_srt

MAX_CHARS = 20_000
MAX_SCENES = 40
_NAME = re.compile(r"[A-Za-z0-9_-]{1,40}")

mcp = _Server(
    "tokenreel",
    instructions=(
        "Turn text or Markdown into short animated, narrated, captioned videos (1080x1920). "
        "Fenced code blocks become code scenes, 'first, then, finally' sentences become flow "
        "diagrams, equations become math cards. Use plan_scenes to preview, render_video to produce an mp4."
    ),
)


def _check(text: str) -> str:
    if not text.strip():
        raise ValueError("text is empty")
    if len(text) > MAX_CHARS:
        raise ValueError(f"text too long ({len(text)} chars, max {MAX_CHARS})")
    return text


def _out_root() -> Path:
    root = Path(os.environ.get("TOKENREEL_OUT", Path.home() / "tokenreel-output")).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


@mcp.tool()
def plan_scenes(text: str) -> list[dict]:
    """Split text or Markdown into scenes. Each scene has a kind (text, flow, math, code),
    its text, keywords and, for flow scenes, numbered steps. No files are written."""
    scenes = plan(_check(text))[:MAX_SCENES]
    return [asdict(s) for s in scenes]


@mcp.tool()
def make_captions(text: str) -> str:
    """Return estimated SRT captions for the text. For exact timings render with narration."""
    return to_srt(estimate_timings(_check(text)))


@mcp.tool()
def render_video(
    text: str,
    name: str = "video",
    narrate: bool = False,
    exact_timings: bool = False,
    burn_captions: bool = False,
) -> dict:
    """Render text to an mp4 plus captions.srt inside the server's output folder.

    narrate: offline Kokoro voiceover (needs the model files, see the README).
    exact_timings: align word times with a local recognizer (needs narrate).
    burn_captions: draw captions into the video.
    Returns the output paths. Requires ffmpeg and the render extra."""
    if not _NAME.fullmatch(name):
        raise ValueError("name must be 1-40 characters of letters, digits, '-' or '_'")
    if exact_timings and not narrate:
        raise ValueError("exact_timings requires narrate=true")
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg was not found on PATH")
    scenes = plan(_check(text))
    if len(scenes) > MAX_SCENES:
        raise ValueError(f"too many scenes ({len(scenes)}, max {MAX_SCENES})")
    if narrate:
        from . import tts

        if not tts.available():
            raise RuntimeError(f"Kokoro model files not found in {tts.MODEL_DIR}")
    from .render import render

    workdir = _out_root() / f"{name}-{uuid.uuid4().hex[:8]}"
    mp4, srt = render(scenes, workdir, f"{name}.mp4", audio=narrate, align=exact_timings, burn=burn_captions)
    return {"video": str(mp4), "captions": str(srt), "scenes": len(scenes), "narrated": narrate}


def main() -> None:
    mcp.run(os.environ.get("TOKENREEL_TRANSPORT", "stdio"))


if __name__ == "__main__":
    main()

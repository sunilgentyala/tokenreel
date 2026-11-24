"""Hardened ffmpeg invocation.

Mitigates the playlist-demuxer SSRF and local-file-read class of bugs
(for example CVE-2023-6605 in the DASH demuxer) by never passing untrusted
URLs to ffmpeg, restricting protocols to `file`, and confining paths to a
working directory. Run inside a container or gVisor for defense in depth.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ALLOWED_SUFFIX = {".png", ".jpg", ".jpeg", ".wav", ".mp3", ".mp4", ".srt", ".vtt"}


class UnsafePath(ValueError):
    pass


def confine(path: str | Path, root: str | Path) -> Path:
    """Resolve path and require it to live under root (blocks traversal and symlink escape)."""
    root_p = Path(root).resolve()
    p = (root_p / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if root_p != p and root_p not in p.parents:
        raise UnsafePath(f"path escapes workdir: {path}")
    if p.suffix.lower() not in ALLOWED_SUFFIX:
        raise UnsafePath(f"file type not allowed: {p.suffix}")
    return p


def build_cmd(inputs: list[str | Path], output: str | Path, root: str | Path, extra: list[str] | None = None) -> list[str]:
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-y"]
    for i in inputs:
        cmd += ["-protocol_whitelist", "file", "-i", str(confine(i, root))]
    cmd += list(extra or [])
    cmd.append(str(confine(output, root)))
    return cmd


def run(cmd: list[str], timeout: int = 300, cwd: str | Path | None = None) -> subprocess.CompletedProcess:
    # list args, no shell, hard timeout
    return subprocess.run(cmd, check=True, capture_output=True, timeout=timeout, shell=False, cwd=cwd)

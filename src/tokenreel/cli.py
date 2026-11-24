import argparse
import json
import sys

from . import __version__
from .segment import plan


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="tokenreel")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan", help="print the scene plan for a text file (JSON)")
    p.add_argument("file")
    c = sub.add_parser("srt", help="print estimated captions (SRT) for a text file")
    c.add_argument("file")
    r = sub.add_parser("render", help="render a silent preview mp4 (needs Pillow and ffmpeg)")
    r.add_argument("file")
    r.add_argument("--out", default="build")
    r.add_argument("--audio", action="store_true", help="narrate offline with Kokoro")
    r.add_argument("--align", action="store_true", help="exact word times via faster-whisper (needs --audio)")
    r.add_argument("--burn", action="store_true", help="burn captions into the video")
    a = ap.parse_args(argv)
    if a.cmd == "plan":
        with open(a.file, encoding="utf-8") as f:
            scenes = plan(f.read())
        json.dump([s.__dict__ for s in scenes], sys.stdout, indent=2)
        print()
    elif a.cmd == "srt":
        from .timing import estimate_timings, to_srt

        with open(a.file, encoding="utf-8") as f:
            print(to_srt(estimate_timings(f.read())))
    elif a.cmd == "render":
        from .render import render

        with open(a.file, encoding="utf-8") as f:
            mp4, srt = render(plan(f.read()), a.out, audio=a.audio, align=a.align, burn=a.burn)
            print(mp4, srt, sep="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

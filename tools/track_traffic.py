"""Snapshot GitHub traffic and audience for this repo into a PRIVATE local store.

GitHub keeps only 14 days of traffic, so run this at least weekly (see
.github/workflows/traffic.yml, which needs a PAT secret named TRAFFIC_TOKEN).
Output goes to METRICS_DIR (default ~/.tokenreel-metrics), never into the repo.
Do not publish these numbers in the README.

Usage: python tools/track_traffic.py OWNER/REPO
"""
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path


def gh(path: str, accept: str | None = None):
    cmd = ["gh", "api", "--paginate", path]
    if accept:
        cmd += ["-H", f"Accept: {accept}"]
    return json.loads(subprocess.run(cmd, check=True, capture_output=True, text=True).stdout or "null")


def main(repo: str) -> None:
    out = Path(os.environ.get("METRICS_DIR", Path.home() / ".tokenreel-metrics"))
    out.mkdir(parents=True, exist_ok=True)
    snap = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "clones": gh(f"repos/{repo}/traffic/clones"),
        "views": gh(f"repos/{repo}/traffic/views"),
        "referrers": gh(f"repos/{repo}/traffic/popular/referrers"),
        "paths": gh(f"repos/{repo}/traffic/popular/paths"),
        "releases": [
            {"tag": r["tag_name"], "downloads": sum(a["download_count"] for a in r["assets"])}
            for r in gh(f"repos/{repo}/releases")
        ],
        "stargazers": [
            {"login": s["user"]["login"], "starred_at": s["starred_at"]}
            for s in gh(f"repos/{repo}/stargazers", "application/vnd.github.star+json")
        ],
        "forks": [f["owner"]["login"] for f in gh(f"repos/{repo}/forks")],
    }
    with open(out / "snapshots.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(snap) + "\n")
    print(f"saved snapshot to {out / 'snapshots.jsonl'}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])

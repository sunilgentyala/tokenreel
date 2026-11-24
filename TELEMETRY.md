# Telemetry

TokenReel collects nothing by default.

If you opt in (`TOKENREEL_TELEMETRY=1` and `TOKENREEL_TELEMETRY_URL=https://...`), one
anonymous ping is sent containing only: tokenreel version, OS family, and Python
major.minor. No text, file names, paths, usernames or identifiers are sent. Setting
`DO_NOT_TRACK=1` always wins. The full payload is in `src/tokenreel/telemetry.py`.

Repository-level adoption is measured from public GitHub signals (traffic, stars, forks,
release downloads), not from user machines.

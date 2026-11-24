# Security Policy

## Reporting a vulnerability

Please do not open a public issue. Use GitHub's **Report a vulnerability** button
(Security tab, private vulnerability reporting) so we get a private fork and a
draft advisory.

## Design stance

- Untrusted text and files are treated as hostile. Paths are confined to a working
  directory and checked against a suffix allow-list.
- ffmpeg is called with list arguments (no shell), `-protocol_whitelist file`, and a
  timeout. Untrusted URLs are never handed to ffmpeg.
- Run rendering in a container, ideally with gVisor, with no network and CPU, memory and
  time limits.
- Releases ship a CycloneDX SBOM, build provenance attestations and Sigstore signatures.
- Telemetry is off by default. See TELEMETRY.md.

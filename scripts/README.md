# Scripts

`scripts/` is the checked-in validation lane for `uHOME-client`.

Current script surfaces include:

- `run-uhome-client-checks.sh` for repo activation validation
- `smoke/` for runtime-safe external-process smoke scripts
- `run-client-server-release-gate.sh` for the hardened client-to-server gate

Boundary rule:

- keep lightweight client-surface checks here
- keep server runtime checks in `uHOME-server`

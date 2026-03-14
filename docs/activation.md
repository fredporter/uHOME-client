# uHOME-client Activation

## Purpose

This document marks the first active implementation tranche for
`uHOME-client`.

The activation goal is to make the public client surfaces teachable,
checkable, and ready for implementation without broadening ownership beyond:

- client-facing interaction modules
- local-network presentation surfaces
- public controller and kiosk examples
- lightweight client contract validation for this repo

## Activated Surfaces

- `src/` as the client module lane
- `scripts/run-uhome-client-checks.sh` as the repo validation entrypoint
- `tests/` as the client contract validation lane
- `config/` as the checked-in client config lane
- `examples/basic-client-session.json` as the smallest client flow example

## Current Validation Contract

Run:

```bash
scripts/run-uhome-client-checks.sh
```

This command:

- verifies the required repo entry surfaces exist
- checks that the sample client session contract is structurally valid
- rejects private local-root path leakage in tracked repo docs and scripts

## Boundaries

This activation does not move ownership into `uHOME-client` for:

- always-on server services
- canonical runtime semantics
- private OMD app behavior
- network provider or control-plane ownership

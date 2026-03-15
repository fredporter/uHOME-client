# uHOME-client Activation

## Purpose

This document marks the first active implementation tranche for
`uHOME-client`.

The activation goal is to make the public client runtime teachable,
checkable, and ready for implementation without broadening ownership beyond:

- lightweight client runtime modules
- local-network runtime-consumption surfaces
- public runtime profile examples
- lightweight client contract validation for this repo
- deployment support for standalone `uHOME` and integrated `uDOS`

## Activated Surfaces

- `src/` as the client runtime module lane
- `scripts/run-uhome-client-checks.sh` as the repo validation entrypoint
- `tests/` as the client contract validation lane
- `config/` as the checked-in client config lane
- `examples/basic-client-runtime.json` as the smallest client runtime example

## Current Validation Contract

Run:

```bash
scripts/run-uhome-client-checks.sh
```

This command:

- verifies the required repo entry surfaces exist
- checks that the sample client runtime contract is structurally valid
- rejects private local-root path leakage in tracked repo docs and scripts

## Boundaries

This activation does not move ownership into `uHOME-client` for:

- always-on server services
- canonical runtime semantics
- Android or iOS app UI behavior
- network provider or control-plane ownership

# uHOME-client

## Purpose

Public client surfaces for local-network home and server interactions.

## Ownership

- client-facing UI and interaction modules
- controller, kiosk, and viewing surfaces
- teachable local-network examples

## Non-Goals

- persistent server runtime ownership
- canonical runtime semantics
- private OMD app ownership

## Spine

- `src/`
- `docs/`
- `tests/`
- `scripts/`
- `config/`
- `examples/`

## Local Development

Keep client flows modular and centered on public contracts.

## Family Relation

uHOME-client consumes uHOME-server and shared uDOS contracts without owning
them.

## Activation

The v2 repo activation path is documented in `docs/activation.md`.
The `v2.0.1` client alignment is documented in
`docs/v2.0.1-client-alignment.md`.

Run the current repo validation entrypoint with:

```bash
scripts/run-uhome-client-checks.sh
```

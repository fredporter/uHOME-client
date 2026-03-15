# uHOME-client

## Purpose

Lightweight client runtime and contract-consumption layer for local-network
uHOME and server interactions.

## Ownership

- lightweight client runtime modules
- contract consumption and runtime endpoint mapping
- teachable local-network session examples
- teachable local-network examples

## Non-Goals

- persistent server runtime ownership
- canonical runtime semantics
- Android or iOS app UI ownership

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
them. UI, kiosk, and platform-specific presentation live in
`uHOME-app-android` and `uHOME-app-ios`.

## Activation

The v2 repo activation path is documented in `docs/activation.md`.
The `v2.0.1` client alignment is documented in
`docs/v2.0.1-client-alignment.md`.

Run the current repo validation entrypoint with:

```bash
scripts/run-uhome-client-checks.sh
```

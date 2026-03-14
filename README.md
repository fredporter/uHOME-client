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

uHOME-client consumes uHOME-server and uDOS contracts without owning them.

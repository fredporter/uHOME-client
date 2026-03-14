# uHOME-client Architecture

uHOME-client provides local-network client surfaces for the family.

## Main Areas

- `src/` stores client modules.
- `examples/` shows public interaction patterns.
- `docs/` explains how clients consume server contracts.
- `scripts/run-uhome-client-checks.sh` is the activation validation entrypoint.

## Contract Edges

- `uHOME-server` owns the always-on runtime and session execution.
- `uDOS-shell` supplies shared shell and routing language for public client
  surfaces.
- `uDOS-wizard` supports assisted or remote routing beyond the local network.
- `uDOS-core` remains the canonical owner of workflow and command semantics.

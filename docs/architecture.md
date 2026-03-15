# uHOME-client Architecture

uHOME-client provides the lightweight local-network client runtime for the
family.

It can run as part of a standalone `uHOME` environment or alongside `uDOS`
when shared family components are present.

## Main Areas

- `src/` stores client-runtime modules and endpoint adapters.
- `examples/` shows public runtime-profile and contract-consumption patterns.
- `docs/` explains how clients consume server contracts.
- `scripts/run-uhome-client-checks.sh` is the activation validation entrypoint.

## Contract Edges

- `uHOME-server` owns the always-on runtime and session execution.
- `uHOME-matter` extends local automation surfaces exposed by the server
  runtime when that extension lane is enabled.
- `uHOME-app-android` and `uHOME-app-ios` own platform UI and kiosk
  presentation on top of this client runtime.
- `uDOS-shell` supplies shared shell and routing language for public client
  surfaces when `uDOS` is present.
- `uDOS-wizard` supports assisted or remote routing beyond the local network.
- `uDOS-core` remains the canonical owner of workflow and command semantics.

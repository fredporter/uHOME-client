# Request: `#binder/uhome-client-activation`

- title: Activate `uHOME-client` as the next Tranche 4 repo-facing implementation surface
- requested by: v2 roadmap workflow
- owning repo or stream: `uHOME-client`
- binder: `#binder/uhome-client-activation`
- summary: Add the first repo-level activation and validation flow for `uHOME-client` while keeping ownership inside client interaction surfaces, local-network presentation modules, and public client examples.
- acceptance criteria:
  - `uHOME-client` exposes an activation doc
  - `uHOME-client` exposes a local validation command under `scripts/`
  - `uHOME-client` includes a minimal client session example
  - repo entry surfaces point to the activation flow
- dependencies:
  - `#binder/core-contract-enforcement`
  - `#binder/plugin-index-activation`
  - `uHOME-client` public repo spine and client-facing docs
- boundary questions:
  - activation should stay inside client ownership
  - server runtime remains in `uHOME-server`
  - canonical semantics remain in `uDOS-core`
- due or milestone: v2 roadmap tranche 4

## Binder Fields

- state: `completed`
- owner: `uHOME-client`
- dependent repos:
  - `uDOS-dev`
- blocked by:
  - none
- target branch: `develop`
- objective:
  - make `uHOME-client` runnable and teachable without broadening its ownership boundary
- promotion criteria:
  - uHOME-client activation docs, example, and validation entrypoint are committed
  - roadmap ledger reflects `uHOME-client` as the active repo-activation binder
- files or areas touched:
  - `uHOME-client/docs`
  - `uHOME-client/src`
  - `uHOME-client/scripts`
  - `uHOME-client/tests`
  - `uHOME-client/config`
  - `uHOME-client/examples`
  - `uDOS-dev/@dev`

## Lifecycle Checklist

- [x] Open
- [x] Hand off
- [x] Advance
- [x] Review
- [x] Commit
- [x] Complete
- [x] Compile
- [x] Promote

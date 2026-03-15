# Source

`src/` is the client runtime module lane for `uHOME-client`.

Current source surfaces include:

- `runtime-profile-contract.json` as the smallest checked-in client runtime
  contract
- `runtime-profile-map.json` as the starter public runtime-profile inventory
- `client_adapter.py` as the starter runtime-target adapter
- `client_adapter.py` also reports the `uDOS-core` runtime-service contracts the
  client consumes during `v2.0.2`
- product runtime-service metadata is loaded from
  `uDOS-core/contracts/runtime-services.json`
- `client_adapter.py` now also derives a runtime-session brief from live
  `uHOME-server` runtime and dashboard surfaces
- the remote-runtime lane now also derives a Wizard-assisted bridge brief from
  shared `/orchestration/dispatch`
- runtime profiles declare both `standalone-uhome` and `integrated-udos`
  deployment modes

Boundary rule:

- keep client runtime contracts here
- keep server-owned runtime behavior in `uHOME-server`

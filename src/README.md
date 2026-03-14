# Source

`src/` is the client module lane for `uHOME-client`.

Current source surfaces include:

- `session-contract.json` as the smallest checked-in client session contract
- `surface-map.json` as the starter public surface inventory
- `client_adapter.py` as the starter runtime-target adapter
- `client_adapter.py` also reports the `uDOS-core` runtime-service contracts the
  client consumes during `v2.0.2`
- product runtime-service metadata is loaded from
  `uDOS-core/contracts/runtime-services.json`
- `client_adapter.py` now also derives a control-session brief from live
  `uHOME-server` runtime and dashboard surfaces

Boundary rule:

- keep client interaction contracts here
- keep server-owned runtime behavior in `uHOME-server`

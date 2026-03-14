# Source

`src/` is the client module lane for `uHOME-client`.

Current source surfaces include:

- `session-contract.json` as the smallest checked-in client session contract
- `surface-map.json` as the starter public surface inventory
- `client_adapter.py` as the starter runtime-target adapter

Boundary rule:

- keep client interaction contracts here
- keep server-owned runtime behavior in `uHOME-server`

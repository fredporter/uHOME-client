# Tests

`tests/` is the client contract validation lane for `uHOME-client`.

Current validation contract:

- `scripts/run-uhome-client-checks.sh` verifies required repo surfaces
- checked-in client runtime-profile contracts must stay structurally valid
- private local-root references must not leak into tracked client docs

Phase 1 rule:

- keep tests lightweight and contract-focused
- use `uHOME-server` for server behavior validation

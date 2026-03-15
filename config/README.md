# Config

`config/` is the checked-in configuration lane for `uHOME-client`.

Family placement rule:

- put checked-in non-secret config templates and config examples here
- put starter runtime payloads and walkthrough samples in `examples/`
- reserve `defaults/` for true reusable checked-in defaults, not one-off
  examples

Current state:

- no separate client config files are required yet
- repo validation is shell and Python standard-library based

Planned use of this root:

- client profile defaults
- runtime adapter and client profile examples

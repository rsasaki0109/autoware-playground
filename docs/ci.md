# CI

The MVP CI model has three tiers:

- `lint`: validates manifests and runs Python tests.
- `smoke`: runs one dry-run planning benchmark and uploads the static report.
- `benchmark-nightly`: placeholder workflow for future pinned Autoware benchmark execution.

CI must not download large assets implicitly. Asset acquisition should stay explicit and checksum-backed.

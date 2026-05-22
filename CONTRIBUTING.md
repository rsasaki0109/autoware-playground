# Contributing

autoware-playground values comparable evidence over standalone implementations. A useful PR should make at least one benchmark easier to reproduce, compare, or diagnose.

## PR Requirements

For experiments:

- declare an Autoware slot in `experiment.yaml`
- prefer `mode: shadow` unless takeover is justified
- include topic interfaces with Autoware message types
- include at least one smoke benchmark
- include known limitations and failure analysis

For benchmarks:

- include `benchmark.yaml`, `metrics.yaml`, `assets.yaml`, and `expected_failures.yaml`
- keep data out of git and reference it with asset manifests
- include baseline results when runnable
- explain threshold changes

## Data Policy

Do not commit large binary assets, private maps, rosbags containing sensitive data, raw dumps, credentials, keys, serial numbers, or identifiers. Use asset manifests with checksums, license, attribution, and privacy fields.

## Review Focus

Reviewers should check:

- manifest validity
- reproducibility metadata
- hidden downloads
- topic and message compatibility
- benchmark evidence
- failure card quality
- whether the change modifies upstream Autoware

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

## Local Real-Path Smoke (rosbag_replay)

For benchmarks whose `runner.type` is `rosbag_replay`, you can exercise the real (non-dry-run) execution path locally without Autoware. Generate a tiny synthetic bag, point `$APG_DATA` at it, then run `apg run` without `--dry-run`:

```bash
python3 tools/scripts/make_sample_rosbag.py /tmp/apg_data/rosbags/sample_lidar_localization_bag
APG_DATA=/tmp/apg_data apg run benchmarks/localization/lidar_localization_replay_001 \
  --experiment experiments/localization/ndt_baseline --headless
```

The resulting `runs/<id>/result.json` carries `execution.baseline_status: real` and metrics gathered from `ros2 bag info` / `ros2 bag play`.

## Review Focus

Reviewers should check:

- manifest validity
- reproducibility metadata
- hidden downloads
- topic and message compatibility
- benchmark evidence
- failure card quality
- whether the change modifies upstream Autoware

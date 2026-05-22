# Autoware Baseline

## What This Method Does

Runs the pinned upstream Autoware stack as the reference experiment for planning benchmarks.

## Paper Summary

This is not a paper method. It exists to make benchmark comparisons explicit and reproducible.

## Autoware Slot

- Slot: `planning.motion`
- Mode: `baseline`
- Upstream ownership: Autoware remains the implementation source.

## Inputs And Outputs

Inputs and outputs are the native Autoware planning simulator interfaces declared in `experiment.yaml`. The playground does not redefine messages.

## How To Run Smoke Benchmark

```bash
apg run benchmarks/planning/lane_change_cut_in_001 \
  --experiment experiments/planning/autoware_baseline \
  --dry-run
```

## Expected Result

Dry-run mode validates manifests and writes a non-executed `RunRecord`.

## Known Failure Modes

- `sim_invalid` when required simulator assets are not present.
- `near_miss` or `planner_oscillation` once real scenario execution is enabled.

## Failure Analysis

Baseline failures should identify whether the failure belongs to Autoware behavior, scenario setup, asset availability, or evaluator configuration.

## Files You Are Allowed To Edit

- `README.md`
- `experiment.yaml`

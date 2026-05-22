# Constant Velocity Baseline

## What This Method Does

Represents a constant-velocity predicted-object baseline for prediction benchmark comparisons.

## Paper Summary

This is not a paper method. It is a lightweight baseline for future learned prediction experiments.

## Autoware Slot

- Slot: `prediction.objects`
- Mode: `shadow`

## Inputs And Outputs

Inputs:

- `/perception/object_recognition/objects`

Outputs:

- `/awpg/experiments/constant_velocity_baseline/objects`

## How To Run Smoke Benchmark

```bash
apg run benchmarks/prediction/cut_in_prediction_001 \
  --experiment experiments/prediction/constant_velocity_baseline \
  --dry-run
```

## Expected Result

Dry-run mode validates manifests and writes a non-executed `RunRecord`.

## Known Failure Modes

- `near_miss` when constant velocity does not model cut-in intent.
- `missed_detection` if required upstream objects are absent.
- `sim_invalid` while scenario assets are placeholder manifests.

## Failure Analysis

Failures should include predicted path error, actor availability, and whether the prediction changed downstream planning TTC.

## Files You Are Allowed To Edit

- `README.md`
- `experiment.yaml`

# NDT Baseline

## What This Method Does

Represents the upstream Autoware NDT localization path as the baseline for localization replay benchmarks.

## Paper Summary

This is not a paper method. It is the pinned Autoware localization baseline used for comparison.

## Autoware Slot

- Slot: `localization.pose_estimator`
- Mode: `offline_replay`

## Inputs And Outputs

Inputs:

- `/sensing/lidar/pointcloud`
- `/initialpose`

Outputs:

- `/localization/kinematic_state`

## How To Run Smoke Benchmark

```bash
apg run benchmarks/localization/lidar_localization_replay_001 \
  --experiment experiments/localization/ndt_baseline \
  --dry-run
```

## Expected Result

Dry-run mode validates manifests and writes a non-executed `RunRecord`.

## Known Failure Modes

- `localization_lost` when pose output is unavailable or jumps.
- `sim_invalid` while replay assets are placeholder manifests.

## Failure Analysis

Failures should capture convergence time, pose jump count, pointcloud availability, and map asset consistency.

## Files You Are Allowed To Edit

- `README.md`
- `experiment.yaml`

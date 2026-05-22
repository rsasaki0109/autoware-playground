# LiDAR Localization Replay 001

## Purpose

This benchmark evaluates localization methods on a fixed LiDAR replay against a map-backed pose estimate contract.

## Autoware Slot

- Primary slot: `localization.pose_estimator`
- Mode: offline replay
- Runner: `rosbag_replay`

## Assets

- Map: `assets/maps/sample_map/asset.yaml`
- Rosbag: `assets/rosbags/sample_lidar_localization/asset.yaml`

## How To Run Smoke Benchmark

```bash
apg run benchmarks/localization/lidar_localization_replay_001 \
  --experiment experiments/localization/icp_registration_toy \
  --dry-run
```

## Expected Result

Dry-run mode validates manifests and writes a `RunRecord` without replaying a rosbag.

When the real runner is connected, the required gates are pose output availability and no localization lost interval.

## Known Failure Modes

- `localization_lost`
- `off_route`
- `sim_invalid`

## Failure Analysis

Failed runs should identify pose jumps, convergence delay, missing pointcloud input, and whether the reference map or replay timing caused the failure.

## Files You Are Allowed To Edit

- `benchmark.yaml`
- `metrics.yaml`
- `assets.yaml`
- `expected_failures.yaml`
- `baselines/ndt_baseline/result.json`

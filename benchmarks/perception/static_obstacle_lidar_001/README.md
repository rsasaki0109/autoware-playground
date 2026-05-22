# Static Obstacle LiDAR 001

## Purpose

This benchmark evaluates whether a LiDAR perception experiment detects a static obstacle in drivable space.

## Autoware Slot

- Primary slot: `perception.objects3d`
- Mode: offline replay
- Runner: `rosbag_replay`

## Assets

- Map: `assets/maps/sample_map/asset.yaml`
- Rosbag: `assets/rosbags/sample_lidar_localization/asset.yaml`

## How To Run Smoke Benchmark

```bash
apg run benchmarks/perception/static_obstacle_lidar_001 \
  --experiment experiments/perception/lidar_cluster_baseline \
  --dry-run
```

## Expected Result

Dry-run mode validates the benchmark and experiment manifests and writes a non-executed `RunRecord`.

When connected to real replay data, the required gates are obstacle detection and no large false positive in drivable area.

## Known Failure Modes

- `missed_detection`
- `near_miss`
- `sim_invalid`

## Failure Analysis

Failed runs should include detection latency, object center error, and whether the relevant obstacle was absent from replay data or missed by the method.

## Files You Are Allowed To Edit

- `benchmark.yaml`
- `metrics.yaml`
- `assets.yaml`
- `expected_failures.yaml`
- `baselines/lidar_cluster_baseline/result.json`

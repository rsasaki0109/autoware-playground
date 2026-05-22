# LiDAR Cluster Baseline

## What This Method Does

Publishes a shadow-mode object candidate stream from classical LiDAR clustering for perception benchmark comparisons.

## Paper Summary

This is not a paper method. It is a simple baseline for comparing learned detector experiments later.

## Autoware Slot

- Slot: `perception.objects3d`
- Mode: `shadow`

## Inputs And Outputs

Inputs:

- `/sensing/lidar/pointcloud`

Outputs:

- `/awpg/experiments/lidar_cluster_baseline/objects`

## How To Run Smoke Benchmark

```bash
apg run benchmarks/perception/static_obstacle_lidar_001 \
  --experiment experiments/perception/lidar_cluster_baseline \
  --dry-run
```

## Expected Result

Dry-run mode validates the launch and parameter references and writes a non-executed `RunRecord`.

## Known Failure Modes

- `missed_detection` for sparse, low-return, or occluded obstacles.
- `sim_invalid` while replay assets are placeholder manifests.

## Failure Analysis

Failures should include pointcloud availability, object center error, false positive area, and threshold values from `params/default.yaml`.

## Files You Are Allowed To Edit

- `README.md`
- `experiment.yaml`
- `launch/lidar_cluster_baseline.launch.py`
- `params/default.yaml`
- `src/`

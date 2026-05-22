# ICP Registration Toy

## What This Method Does

Publishes a shadow-mode candidate pose estimate from a toy ICP-style registration path.

## Paper Summary

This is a small MVP localization experiment, not a production localizer. It exists to exercise the experiment manifest, replay benchmark, and report flow.

## Autoware Slot

- Slot: `localization.pose_estimator`
- Mode: `offline_replay`

## Inputs And Outputs

Inputs:

- `/sensing/lidar/pointcloud`
- `/map/pointcloud_map`
- `/initialpose`

Outputs:

- `/awpg/experiments/icp_registration_toy/pose`

## How To Run Smoke Benchmark

```bash
apg run benchmarks/localization/lidar_localization_replay_001 \
  --experiment experiments/localization/icp_registration_toy \
  --dry-run
```

## Expected Result

Dry-run mode validates the launch and parameter references and writes a non-executed `RunRecord`.

## Known Failure Modes

- `localization_lost` if registration does not converge.
- `off_route` if the estimated pose drifts outside the route corridor.
- `sim_invalid` while replay assets are placeholder manifests.

## Failure Analysis

Failures should include the first valid pose time, pose jump count, and the pointcloud interval used for registration.

## Files You Are Allowed To Edit

- `README.md`
- `experiment.yaml`
- `launch/icp_registration_toy.launch.py`
- `params/default.yaml`
- `src/`

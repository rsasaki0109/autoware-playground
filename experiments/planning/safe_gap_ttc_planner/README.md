# Safe Gap TTC Planner

## What This Method Does

Publishes a shadow-mode candidate trajectory that rejects lane-change gaps when predicted-object TTC is below a configurable threshold.

## Paper Summary

This is a toy paper-style planner for MVP integration. It demonstrates how a small research method can connect to Autoware-native topics and be compared against the same benchmark as the baseline.

## Autoware Slot

- Slot: `planning.motion`
- Mode: `shadow`
- Output namespace: `/awpg/experiments/safe_gap_ttc_planner`

## Inputs And Outputs

Inputs:

- `/planning/scenario_planning/trajectory`
- `/perception/object_recognition/objects`
- `/localization/kinematic_state`

Outputs:

- `/awpg/experiments/safe_gap_ttc_planner/trajectory`

## How To Run Smoke Benchmark

```bash
apg run benchmarks/planning/lane_change_cut_in_001 \
  --experiment experiments/planning/safe_gap_ttc_planner \
  --headless \
  --dry-run
```

## Expected Result

Dry-run mode validates the launch and parameter references and writes a non-executed `RunRecord`.

## Known Failure Modes

- `near_miss` if TTC filtering is too permissive.
- `planner_oscillation` if the gap decision toggles between frames.
- `sim_invalid` while only placeholder scenario assets are available.

## Failure Analysis

Failures should include the target actor track, min TTC timeline, and whether trajectory changes were caused by input prediction noise or threshold selection.

## Files You Are Allowed To Edit

- `README.md`
- `experiment.yaml`
- `launch/safe_gap_ttc_planner.launch.py`
- `params/default.yaml`
- `src/`

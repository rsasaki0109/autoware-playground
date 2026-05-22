# Cut-In Prediction 001

## Purpose

This benchmark evaluates predicted object trajectories for a vehicle preparing to cut into ego's lane.

## Autoware Slot

- Primary slot: `prediction.objects`
- Mode: shadow
- Runner: `scenario_simulator_v2`

## Assets

- Map: `assets/maps/sample_map/asset.yaml`
- Scenario: `assets/scenarios/sample_lane_change/asset.yaml`

## How To Run Smoke Benchmark

```bash
apg run benchmarks/prediction/cut_in_prediction_001 \
  --experiment experiments/prediction/constant_velocity_baseline \
  --dry-run
```

## Expected Result

Dry-run mode validates manifests and writes a `RunRecord` without launching Scenario Simulator v2.

When real scenario execution is connected, the required gate is prediction topic availability.

## Known Failure Modes

- `near_miss`
- `missed_detection`
- `sim_invalid`

## Failure Analysis

Failed runs should include predicted path error, collision risk under prediction, and whether planning TTC changed because of the predicted object output.

## Files You Are Allowed To Edit

- `benchmark.yaml`
- `metrics.yaml`
- `assets.yaml`
- `expected_failures.yaml`
- `baselines/constant_velocity_baseline/result.json`

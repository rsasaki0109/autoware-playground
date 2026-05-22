# Lane Change Cut-In 001

## Purpose

This benchmark evaluates planning behavior when ego begins a lane change and a target-lane vehicle cuts into the available gap.

## Autoware Slot

- Primary slot: `planning.motion`
- Mode: shadow first
- Runner: `scenario_simulator_v2`

## Assets

- Map: `assets/maps/sample_map/asset.yaml`
- Scenario: `assets/scenarios/sample_lane_change/asset.yaml`
- Rosbag: not used

The referenced assets are manifests only. No map, rosbag, or scenario binary data is stored in git.

## How To Run Smoke Benchmark

```bash
apg run benchmarks/planning/lane_change_cut_in_001 \
  --experiment experiments/planning/safe_gap_ttc_planner \
  --headless \
  --dry-run
```

## Expected Result

Dry-run mode validates the benchmark, validates the selected experiment, creates a run directory, writes `result.json`, and generates a static report without launching Autoware or Scenario Simulator v2.

When the real runner is connected, the required gates are no collision and at least 95 percent route completion.

## Known Failure Modes

- `collision`
- `near_miss`
- `planner_oscillation`
- `deadlock`
- `sim_invalid`

## Failure Analysis

Failed runs should include the time interval around the cut-in, min TTC trend, ego trajectory overlay, and whether the failure is due to the baseline scenario, candidate planner output, or simulator setup.

## Files You Are Allowed To Edit

- `benchmark.yaml`
- `metrics.yaml`
- `assets.yaml`
- `expected_failures.yaml`
- `scenario/scenario.yaml`
- `baselines/autoware_baseline/result.json`

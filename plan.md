# autoware-playground plan

Date: 2026-05-22

This document is the restart point for building `autoware-playground`.

The repository should be designed as an experiment and benchmark overlay on top of an Autoware workspace. It is not an Autoware Universe alternative, not a fork, and not a smaller Autoware. Autoware Core and Universe remain the upstream autonomy stack. autoware-playground sits outside them and provides a benchmark-first place to connect research implementations to Autoware-native interfaces.

## 1. One-Sentence Philosophy

autoware-playground is a benchmark-first experimentation commons for Autoware-native research implementations.

The repo's center of value is not just "paper code that runs". The repo should value "paper code that can be compared under the same scenario, same rosbag, same map, and same metrics".

This means every useful contribution should make at least one of these things better:

- the set of reusable experiment slots
- the set of reproducible benchmark cases
- the quality of run records
- the quality of failure analysis
- the ease of comparing future paper methods

## 2. What This Repo Does

The repo should focus on four first-class concepts.

### Experiment Slot

An experiment slot is a light contract for connecting a paper method to an Autoware pipeline area such as planning, perception, localization, or prediction.

It is not a framework. It is not a plugin SDK. It is not a new API that replaces Autoware topics or messages.

It says:

- this type of method reads these existing Autoware-compatible topics
- this type of method publishes this candidate output
- this output can be evaluated in shadow mode
- this output may later be remapped in takeover mode when appropriate

### Benchmark Case

A benchmark case is the smallest reusable evaluation unit.

It should bundle:

- scenario or rosbag
- map
- vehicle and sensor model
- metric config
- expected failure tags
- baseline result
- reproducibility metadata

The benchmark case should be stored under `benchmarks/<task>/<case_name>/`.

### Run Record

A run record is the exact output of one experiment on one benchmark.

It should include:

- autoware-playground commit
- Autoware version or lock reference
- container digest when available
- ROS distribution
- asset hashes
- metrics
- failures
- artifacts
- reproduce command

This should be written as JSON so it can be validated and compared.

### Failure Card

A failure card records why a benchmark failed and how that failure can become a future benchmark.

It should include:

- benchmark name
- experiment name
- failure tag
- time range
- symptoms
- relevant artifacts
- suggested scenario mutations

The repo should treat failure cards as assets, not as embarrassing leftovers. This is how failed runs strengthen the ecosystem.

## 3. What This Repo Explicitly Does Not Do

Avoid these by default:

- do not create a mini Autoware
- do not fork or replace Autoware Universe
- do not create an independent planning framework
- do not create a custom simulator
- do not redefine Autoware messages
- do not add a large shared plugin SDK in MVP
- do not build a web dashboard or MLOps platform in MVP
- do not accept "implementation only" PRs as the normal path
- do not accept "benchmark-less" PRs as the normal path
- do not store large maps, rosbags, model weights, or raw datasets in git

## 4. Success Loop

The desired repo loop is:

```text
new paper implementation
  -> runs existing benchmarks
  -> adds method card + result record
  -> exposes failures
  -> failure becomes new scenario
  -> benchmark suite becomes stronger
  -> future papers become easier to compare
```

This is the main reason for the repo to exist. Every new implementation should add comparison value beyond its own code.

## 5. Architecture Principles

### Principle 1: Autoware-Native, Not Autoware-Like

Respect Autoware topics, messages, launch patterns, maps, scenario execution, and rosbag replay.

Wrong direction:

```text
playground defines its own planner API
```

Right direction:

```text
playground defines a planning experiment slot
that must publish/subscribe Autoware-compatible topics
```

### Principle 2: Benchmark-First

The PR unit should be:

```text
algorithm + manifest + at least one benchmark run + failure analysis
```

The repo should avoid claims like "this method works" without evidence. A useful contribution says something concrete:

- this scenario improves minimum TTC over baseline
- this rosbag exposes slow localization convergence
- this cut-in case causes planner oscillation
- this perception method misses a static obstacle under these conditions

### Principle 3: Scenario-First

For closed-loop planning and behavior evaluation, scenario definitions should be the comparison anchor.

The intended minimum unit is:

```text
benchmarks/planning/lane_change_cut_in_001/
  scenario/
  benchmark.yaml
  metrics.yaml
  assets.yaml
  expected_failures.yaml
  baselines/
```

### Principle 4: Minimal Viable Interfaces

The first stable interfaces should be only:

- `ExperimentManifest`
- `BenchmarkManifest`
- `RunRecord`

Supporting manifests can exist for assets and metrics, but the main interface surface should remain small.

Do not create a common C++ base class, global ROS plugin registry, or generic simulator abstraction in MVP.

### Principle 5: Shadow Mode First, Takeover Mode Second

Research methods should not need to control ego vehicle at first.

Shadow mode:

```text
Autoware baseline drives
experiment publishes candidate output
evaluator compares candidate output
```

Takeover mode:

```text
experiment replaces one Autoware module
ego uses experiment output
```

MVP should strongly prefer shadow mode. This keeps learned planners, VLM driving, world-model planners, and fragile paper implementations comparable without making them responsible for safety-critical control.

### Principle 6: Failure-Analysis-First

Every benchmark run should classify failures with structured tags.

Initial tags:

```yaml
failure_tags:
  - collision
  - near_miss
  - deadlock
  - off_route
  - localization_lost
  - missed_detection
  - planner_oscillation
  - sim_invalid
```

The output of a failed run should seed future scenarios and benchmark mutations.

## 6. MVP Name And Scope

MVP name:

```text
MVP 0.1: Benchmark-first Autoware Experiment Overlay
```

MVP must finish:

- `apg` CLI
- experiment manifests
- benchmark manifests
- run record JSON output
- asset manifests
- metric config manifests
- first planning benchmark
- first localization replay benchmark
- first perception benchmark
- baseline experiment
- one toy paper-style planning experiment
- static HTML report generation
- CI schema/smoke workflow

MVP must not include:

- web dashboard
- full leaderboard
- cloud evaluator
- generic plugin framework
- custom simulator
- custom messages
- large public dataset hosting
- full VLM/world-model implementation
- production-quality CI matrix

## 7. First Directory Layout

Target layout:

```text
autoware-playground/
  README.md
  AGENTS.md
  CONTRIBUTING.md
  LICENSE
  CODEOWNERS
  plan.md

  .github/
    workflows/
      lint.yaml
      smoke.yaml
      benchmark-nightly.yaml
    pull_request_template.md

  .devcontainer/
    devcontainer.json

  docker/
    Dockerfile
    compose.yaml
    entrypoint.sh

  repositories/
    autoware-playground.repos
    autoware-pinned.lock.yaml

  schemas/
    experiment.schema.json
    benchmark.schema.json
    asset.schema.json
    metric.schema.json
    result.schema.json

  tools/
    apg/
      pyproject.toml
      apg/
        __init__.py
        cli.py
        run.py
        compare.py
        assets.py
        report.py
        schema.py

  ros2_packages/
    awpg_runner/
    awpg_metrics/
    awpg_report/
    awpg_rosbag_tools/
    awpg_scenario_tools/

  contracts/
    README.md
    failure_taxonomy.yaml
    slots/
      localization.pose_estimator.md
      perception.objects3d.md
      perception.occupancy_grid.md
      prediction.objects.md
      planning.behavior.md
      planning.motion.md
      planning.trajectory.md
    topics/
      common_topics.md

  benchmarks/
    planning/
      lane_change_cut_in_001/
        README.md
        benchmark.yaml
        scenario/
          scenario.yaml
        metrics.yaml
        assets.yaml
        expected_failures.yaml
        baselines/
          autoware_baseline/
            result.json
    localization/
      lidar_localization_replay_001/
        README.md
        benchmark.yaml
        metrics.yaml
        assets.yaml
        expected_failures.yaml
    perception/
      static_obstacle_lidar_001/
        README.md
        benchmark.yaml
        metrics.yaml
        assets.yaml
        expected_failures.yaml
    prediction/
      cut_in_prediction_001/
        README.md
        benchmark.yaml
        metrics.yaml
        assets.yaml
        expected_failures.yaml

  experiments/
    planning/
      autoware_baseline/
        README.md
        experiment.yaml
      safe_gap_ttc_planner/
        README.md
        experiment.yaml
        launch/
        params/
        src/
    localization/
      ndt_baseline/
        README.md
        experiment.yaml
      icp_registration_toy/
        README.md
        experiment.yaml
        launch/
        params/
        src/
    perception/
      lidar_cluster_baseline/
        README.md
        experiment.yaml
        launch/
        params/
        src/
    prediction/
      constant_velocity_baseline/
        README.md
        experiment.yaml

  assets/
    README.md
    maps/
      sample_map/
        asset.yaml
    rosbags/
      sample_lidar_localization/
        asset.yaml
    scenarios/
      sample_lane_change/
        asset.yaml

  reports/
    README.md

  runs/
    .gitignore

  docs/
    quickstart.md
    adding_a_paper_method.md
    adding_a_benchmark.md
    reproducibility.md
    ci.md
    benchmark_cards/

  tests/
```

Why this layout works:

- `experiments/` is where paper methods enter.
- `benchmarks/` is where comparison conditions enter.
- `contracts/` is where humans and AI agents read interface agreements.
- `assets/` stores manifests, not data.
- `runs/` stores generated output and is not committed by default.
- `tools/apg/` can evolve without forcing ROS package build logic into every workflow.

## 8. Minimal Manifest Designs

### Experiment Manifest

Example:

```yaml
api_version: apg/v0
kind: Experiment

name: safe_gap_ttc_planner
task: planning
slot: planning.motion
mode: shadow

paper:
  title: "Safe Gap Selection for Lane Change under Cut-in Risk"
  venue: "example"
  year: 2026
  url: null

autoware:
  tested_with:
    autoware_lock: repositories/autoware-pinned.lock.yaml

interfaces:
  inputs:
    - topic: /planning/scenario_planning/trajectory
      type: autoware_planning_msgs/msg/Trajectory
    - topic: /perception/object_recognition/objects
      type: autoware_perception_msgs/msg/PredictedObjects
    - topic: /localization/kinematic_state
      type: nav_msgs/msg/Odometry
  outputs:
    - topic: /awpg/experiments/safe_gap_ttc_planner/trajectory
      type: autoware_planning_msgs/msg/Trajectory

launch:
  package: awpg_safe_gap_ttc_planner
  file: launch/safe_gap_ttc_planner.launch.py
  params:
    - params/default.yaml

benchmarks:
  smoke:
    - benchmarks/planning/lane_change_cut_in_001
  recommended:
    - benchmarks/planning/occluded_pedestrian_stop_001

reproducibility:
  random_seed: 42
  deterministic: true
```

### Benchmark Manifest

Example:

```yaml
api_version: apg/v0
kind: Benchmark

name: lane_change_cut_in_001
task: planning
description: >
  Ego performs lane change while a target-lane vehicle cuts in.

runner:
  type: scenario_simulator_v2
  headless: true
  timeout_sec: 180
  scenario: scenario/scenario.yaml

assets:
  map: assets/maps/sample_map/asset.yaml
  scenario: assets/scenarios/sample_lane_change/asset.yaml
  rosbag: null

autoware:
  launch:
    package: autoware_launch
    file: planning_simulator.launch.xml
  vehicle_model: sample_vehicle
  sensor_model: sample_sensor_kit

metrics:
  config: metrics.yaml

gates:
  required:
    - name: no_collision
      op: "=="
      value: true
    - name: route_completion
      op: ">="
      value: 0.95
  diagnostic:
    - name: min_ttc_sec
      op: ">="
      value: 1.5
    - name: max_jerk_mps3
      op: "<="
      value: 4.0

failure_taxonomy:
  - collision
  - near_miss
  - planner_oscillation
  - deadlock
```

### Run Record

Example:

```json
{
  "api_version": "apg/v0",
  "kind": "RunRecord",
  "run_id": "2026-05-22T10-30-00Z_lane_change_cut_in_safe_gap",
  "experiment": "safe_gap_ttc_planner",
  "benchmark": "lane_change_cut_in_001",
  "mode": "shadow",
  "git": {
    "autoware_playground": "abc123",
    "autoware_universe": "def456"
  },
  "runtime": {
    "container_digest": "sha256:...",
    "ros_distro": "pinned-by-lockfile"
  },
  "assets": {
    "map_sha256": "...",
    "scenario_sha256": "..."
  },
  "metrics": {
    "no_collision": true,
    "route_completion": 0.98,
    "min_ttc_sec": 2.1,
    "max_jerk_mps3": 3.6
  },
  "failures": [],
  "artifacts": {
    "rosbag": "runs/.../output.bag",
    "report": "runs/.../report.html",
    "plots": "runs/.../plots/"
  },
  "reproduce": "apg run benchmarks/planning/lane_change_cut_in_001 --experiment experiments/planning/safe_gap_ttc_planner --seed 42"
}
```

## 9. Autoware Integration Policy

The repo should use slot-based integration.

A slot is only a contract:

```text
this experiment kind reads these inputs
this experiment kind writes these outputs
these outputs are evaluated this way
```

It is not a runtime framework.

Initial slots:

| Slot | Target | MVP mode | Policy |
|---|---|---|---|
| `localization.pose_estimator` | NDT, ICP, LIO, GNSS fusion | shadow / takeover / offline replay | produce ego pose from map, sensor, and initial pose |
| `perception.objects3d` | LiDAR detector, fusion detector | shadow | publish objects and compare to baseline or reference |
| `perception.occupancy_grid` | occupancy grid, freespace | shadow | evaluate grid quality before using it in planning |
| `prediction.objects` | constant velocity, neural prediction | shadow | compare predicted objects and future trajectories |
| `planning.behavior` | lane change, avoidance, yield, stop | shadow / takeover | compare behavior decision or candidate path |
| `planning.motion` | trajectory optimization, learned planner | shadow / takeover | compare trajectory quality |
| `planning.trajectory` | end-to-end planner, VLM/world model planner | shadow first | publish candidate trajectory and optional explanation |

## 10. Integration Modes

### Baseline Mode

Run Autoware Universe itself as the baseline.

```text
experiment = autoware_baseline
benchmark = lane_change_cut_in_001
```

Every benchmark should eventually have a baseline run record.

### Shadow Mode

The paper method subscribes to Autoware-compatible inputs and publishes candidate output under `/awpg/experiments/...`.

```text
Autoware baseline drives ego
paper method publishes candidate trajectory
evaluator compares baseline trajectory vs candidate trajectory
```

This should be the default mode in MVP.

### Takeover Mode

The paper method replaces one Autoware module by disabling the original node and remapping output to the expected Autoware topic.

MVP should support this only in narrow planning/localization cases after shadow-mode evidence exists.

### Offline Replay Mode

Replay rosbag data to evaluate perception, localization, or prediction methods.

This mode should preserve Autoware's rosbag replay patterns rather than inventing a universal simulator API.

## 11. Asset, Metric, And Failure Management

Do not manage rosbags, maps, scenarios, and metrics as unrelated files. Manage them as a benchmark case bundle.

```text
benchmark case =
  scenario or rosbag
  + map
  + vehicle/sensor model
  + metric config
  + expected failure tags
  + baseline result
  + reproducibility metadata
```

### Asset Manifest

Example:

```yaml
api_version: apg/v0
kind: Asset

name: sample_lidar_localization_bag
type: rosbag
version: 0.1.0

source:
  uri: "s3://example-or-public-url/sample_lidar_localization_bag.tar.zst"
  license: "CC-BY-4.0"
  attribution: "Example Dataset Provider"

integrity:
  sha256: "..."
  size_bytes: 123456789

layout:
  unpack_to: "$APG_DATA/rosbags/sample_lidar_localization_bag"
  rosbag_storage: sqlite3

privacy:
  contains_faces: false
  contains_license_plates: false
  anonymized: true

used_by:
  - benchmarks/localization/lidar_localization_replay_001
```

### Metric Config

Example:

```yaml
api_version: apg/v0
kind: MetricConfig

sources:
  - name: autoware_planning_evaluator
    type: ros2_node
  - name: awpg_offline_metrics
    type: python

metrics:
  no_collision:
    source: scenario_result
    type: boolean

  min_ttc_sec:
    source: autoware_planning_evaluator
    reducer: min
    required: false

  route_completion:
    source: awpg_offline_metrics
    topic: /localization/kinematic_state
    reducer: final

  max_jerk_mps3:
    source: autoware_planning_evaluator
    reducer: max

report:
  plots:
    - ego_speed
    - min_ttc
    - lateral_acceleration
    - trajectory_overlay
```

### Failure Card

Example:

```yaml
failure:
  benchmark: lane_change_cut_in_001
  experiment: safe_gap_ttc_planner
  tag: planner_oscillation
  time_range_sec: [42.1, 48.7]
  symptoms:
    - repeated trajectory lateral shift
    - blinker toggled frequently
    - min_ttc decreased below diagnostic threshold
  artifacts:
    rosbag: runs/.../failure_segment.bag
    plot: runs/.../plots/min_ttc.png
    rviz_config: runs/.../debug.rviz
  suggested_next_scenarios:
    - increase cut-in speed
    - reduce target-lane gap
```

## 12. Runner Architecture

`apg run` should follow this sequence:

```text
apg run benchmark
  1. validate benchmark.yaml
  2. validate experiment.yaml
  3. fetch assets by checksum
  4. create run directory
  5. launch Autoware
  6. launch experiment
  7. run scenario_simulator_v2 or rosbag replay
  8. collect logs, bags, evaluator outputs
  9. compute offline metrics
 10. classify failures
 11. generate report.html
 12. write result.json
```

MVP should initially implement:

- `apg validate`
- `apg list benchmarks`
- `apg list experiments`
- `apg run --dry-run`
- `apg report`

Then extend `apg run` to invoke real runner backends.

## 13. Evaluation Layers

Do not build one giant metric engine.

Use three layers:

```text
Layer 1: simulator/scenario result
  collision, goal reached, timeout, rule violation

Layer 2: Autoware evaluators
  planning metrics, control metrics, trajectory stability, TTC, jerk

Layer 3: playground offline metrics
  benchmark-specific metrics, report plots, failure tags
```

## 14. Simulation Policy

Avoid over-abstracting simulation in MVP.

Use runner type, not a universal simulator API:

```yaml
runner:
  type: scenario_simulator_v2
```

```yaml
runner:
  type: rosbag_replay
```

Initial runner priorities:

| Runner | MVP priority | Use |
|---|---:|---|
| `scenario_simulator_v2` | 1 | planning and behavior closed-loop scenarios |
| `rosbag_replay` | 1 | localization, perception, prediction replay |
| `planning_simulator` | 2 | lightweight planning module tests |
| `awsim` | 3 | richer digital-twin demo |
| `carla`, `morai`, others | later | community backends |

## 15. First Benchmark Targets

### B001: planning/lane_change_cut_in_001

Purpose:

- behavior planning and motion planning comparison

Runner:

- `scenario_simulator_v2`

Mode:

- shadow first
- takeover later

Metrics:

- required: `no_collision`, `route_completion`
- diagnostic: `min_ttc_sec`, `max_jerk_mps3`, `lateral_acceleration`, `trajectory_stability`, `planner_oscillation`

Why first:

- strong demo
- trajectory, TTC, jerk, route completion are easy to explain
- good fit for Autoware baseline vs toy paper-style planner comparison

### B002: planning/occluded_pedestrian_stop_001

Purpose:

- perception-aware planning and failure analysis

Runner:

- `scenario_simulator_v2`

Metrics:

- required: `no_collision`, `stop_before_conflict_area`
- diagnostic: `stopping_margin_m`, `time_to_resume_sec`, `max_deceleration_mps2`, `deadlock_duration_sec`

### B003: localization/lidar_localization_replay_001

Purpose:

- NDT, ICP, LiDAR localization, GNSS fusion comparison

Runner:

- `rosbag_replay`

Metrics:

- required: `pose_output_available`, `no_localization_lost`
- diagnostic: `ate_m`, `rpe_m`, `convergence_time_sec`, `pose_jump_count`, `cpu_time_ms`

### B004: perception/static_obstacle_lidar_001

Purpose:

- LiDAR detector and occupancy grid comparison

Runner:

- `rosbag_replay` or `scenario_simulator_v2`

Metrics:

- required: `obstacle_detected`, `no_large_false_positive_in_drivable_area`
- diagnostic: `detection_latency_ms`, `object_center_error_m`, `occupancy_iou`, `missed_detection_count`

### B005: prediction/cut_in_prediction_001

Purpose:

- prediction algorithm comparison

Runner:

- `scenario_simulator_v2`

Metrics:

- required: `prediction_topic_available`
- diagnostic: `minADE`, `minFDE`, `collision_risk_under_prediction`, `planner_ttc_with_prediction`

## 16. First Experiments And Utilities

### experiments/planning/autoware_baseline

No paper implementation. This runs the pinned Autoware baseline and provides the reference result for benchmarks.

### experiments/planning/safe_gap_ttc_planner

A toy but visually useful paper-style motion planning example.

Inputs:

- baseline trajectory
- predicted objects
- ego odometry

Output:

- candidate trajectory under `/awpg/experiments/safe_gap_ttc_planner/trajectory`

Mode:

- shadow

Purpose:

- demonstrate how a paper planner can be added as a small PR

### experiments/localization/icp_registration_toy

Minimal localization experiment.

Inputs:

- pointcloud
- map
- initial pose

Output:

- candidate pose

Purpose:

- compare against NDT baseline on replay data

### experiments/perception/lidar_cluster_baseline

Classical clustering baseline for learned detector comparisons.

### experiments/prediction/constant_velocity_baseline

Minimum prediction baseline for future neural prediction PRs.

### experiments/failure_analysis/min_ttc_miner

Utility to mine risky intervals from failed runs.

Inputs:

- run rosbag
- metric timeline

Outputs:

- failure segment
- failure card
- suggested scenario mutation

## 17. AI-Agent-Friendly Repository Rules

Root `AGENTS.md` should say:

```text
This repository is an Autoware experimentation overlay.
Do not create a mini Autoware.
Do not redefine Autoware messages.
Do not edit upstream Autoware repositories.
```

Every experiment must include:

- `README.md`
- `experiment.yaml`
- launch file or explicit reason why not needed
- `params/default.yaml` if parameters exist
- at least one benchmark result or smoke benchmark
- known limitations
- failure analysis section

Every benchmark must include:

- `benchmark.yaml`
- `metrics.yaml`
- `assets.yaml`
- `README.md`
- `expected_failures.yaml`
- baseline result if runnable

Preferred implementation style:

- small files
- explicit launch/remap/params
- no hidden downloads
- no global refactor
- shadow mode before takeover mode
- tests for schema and CLI behavior
- reproducible benchmarks

Forbidden by default:

- modifying upstream Autoware source directly
- adding large binary assets to git
- introducing a new simulator abstraction
- adding custom ROS messages unless approved
- changing benchmark thresholds without explaining why

Experiment READMEs should follow this order:

1. What this method does
2. Paper summary
3. Autoware slot
4. Inputs and outputs
5. How to run smoke benchmark
6. Expected result
7. Known failure modes
8. Files you are allowed to edit

## 18. Paper-To-PR Flow

Target flow:

```text
1. apg create experiment planning my_paper_planner
2. agent reads:
   - AGENTS.md
   - contracts/slots/planning.motion.md
   - benchmarks/planning/lane_change_cut_in_001/README.md
3. agent implements shadow-mode node
4. apg lint
5. apg run benchmarks/planning/lane_change_cut_in_001 --experiment my_paper_planner
6. apg report runs/latest
7. PR includes:
   - method card
   - result.json
   - failure card if failed
```

Useful commands:

```bash
apg list benchmarks
apg list experiments
apg validate experiments/planning/safe_gap_ttc_planner
apg run benchmarks/planning/lane_change_cut_in_001 \
  --experiment experiments/planning/safe_gap_ttc_planner \
  --headless
apg compare runs/baseline runs/safe_gap
apg report runs/safe_gap
```

## 19. PR Template

Initial `.github/pull_request_template.md`:

```markdown
## What is added?

- [ ] experiment
- [ ] benchmark
- [ ] metric
- [ ] failure analysis tool
- [ ] docs only

## Autoware slot

Example: `planning.motion`

## Mode

- [ ] shadow
- [ ] takeover
- [ ] offline replay

## Benchmarks run

| benchmark | result | report |
|---|---|---|

## Known failures

## Repro command

```bash
apg run ...
```

## Did you modify upstream Autoware?

- [ ] no
- [ ] yes, explain why
```

## 20. CI/CD Strategy

Use pinned `.repos` and lock files for reproducibility.

### Tier 1: PR Lint

Every PR:

- YAML and JSON schema validation
- Python lint
- Markdown lint
- experiment manifest validation
- benchmark manifest validation
- asset checksum format validation
- no large binary files
- no forbidden path modifications

### Tier 2: PR Smoke

Small headless or dry-run benchmark:

- build minimal `awpg_*` packages when available
- run one tiny benchmark
- produce `result.json`
- upload `report.html`

No GPU. No large bags. No GUI.

### Tier 3: Nightly Benchmark

Nightly:

- pinned Autoware workspace
- selected benchmark matrix
- baseline experiment
- selected community experiments
- report artifacts
- regression summary

### Tier 4: Weekly Extended Benchmark

Weekly or manual:

- larger rosbags
- AWSIM cases
- GPU perception cases
- VLM/world-model shadow-mode cases

### CI Gates

Must pass:

- schemas
- smoke benchmark
- reproducibility metadata
- no hidden data
- no upstream Autoware edits

May fail but must report:

- experimental benchmark scores
- diagnostic metric thresholds

Research velocity should not be killed by requiring every experimental method to pass every benchmark. Failed benchmark results are acceptable when they are structured and useful.

## 21. First Impressive Demo

Demo name:

```text
One command: reproduce a lane-change failure and compare a paper-style planner against Autoware baseline.
```

Command:

```bash
apg demo lane_change_cut_in \
  --experiments autoware_baseline,safe_gap_ttc_planner \
  --headless \
  --report
```

What it shows:

1. Scenario Simulator v2 runs lane-change cut-in scenario.
2. Autoware baseline drives ego.
3. `safe_gap_ttc_planner` runs in shadow mode.
4. Metrics are collected.
5. `report.html` shows pass/fail gates, trajectory overlay, min TTC curve, jerk curve, route completion, and failure cards.
6. `result.json` contains exact reproduce command.

Why this demo matters:

```text
A paper method can be added as a small PR.
It plugs into Autoware.
It runs the same scenario as baseline.
It produces comparable metrics.
It exposes failures.
Those failures become new benchmark cases.
```

## 22. MVP 0.1 Acceptance Criteria

### Repo

- README-driven quickstart exists
- `AGENTS.md` exists
- schemas exist
- docker/devcontainer exists
- pinned repository files exist

### Runner

- `apg validate` works
- `apg run --dry-run` works for at least one scenario benchmark
- `apg run --dry-run` works for at least one rosbag replay benchmark
- `apg report` generates static HTML

### Benchmarks

- `planning/lane_change_cut_in_001`
- `localization/lidar_localization_replay_001`
- `perception/static_obstacle_lidar_001`

### Experiments

- `autoware_baseline`
- `safe_gap_ttc_planner`
- `icp_registration_toy`
- `lidar_cluster_baseline`
- `constant_velocity_baseline`

### Reproducibility

- every run writes `result.json`
- every asset has SHA-256 field
- every result has Autoware lock reference
- every report includes reproduce command

### CI

- lint workflow
- schema workflow
- one headless or dry-run smoke benchmark
- report artifact upload

## 23. MVP 0.1 Non-Goals

- no full leaderboard
- no cloud evaluator
- no large dataset hosting
- no custom simulator
- no generalized plugin SDK
- no production takeover of all Autoware modules
- no full VLM/world-model implementation

## 24. README Structure

Root README should follow this order:

```text
# autoware-playground

Autoware-native experimentation and benchmark playground.

## What this is

## What this is not

## 5-minute demo

## Core concepts
- Experiment
- Benchmark
- Asset
- Metric
- RunRecord
- FailureCard

## Add a paper method

## Add a benchmark

## Current benchmark suites

## Current experiments

## Reproducibility model

## CI model

## Contribution rules
```

Recommended opening:

```text
autoware-playground is not a smaller Autoware.
It is a place to plug research methods into Autoware,
run them against shared scenarios and rosbags,
and turn both successes and failures into reusable benchmarks.
```

## 25. First 10 Issues

Create issues in this order:

1. Create README philosophy and non-goals
2. Add AGENTS.md for AI coding agents
3. Add experiment / benchmark / asset / result JSON schemas
4. Implement `apg validate`
5. Implement `apg run` skeleton
6. Add `planning/lane_change_cut_in_001` benchmark
7. Add `autoware_baseline` experiment
8. Add `safe_gap_ttc_planner` shadow-mode example
9. Generate static `report.html` from `result.json`
10. Add GitHub Actions smoke benchmark

This order keeps the repository benchmark-first from the beginning.

## 26. Current Local State After MVP Dry-Run Pass

Updated on 2026-05-22 after the seventh MVP implementation pass (CI now runs the real (non-dry-run) rosbag_replay path end-to-end on GitHub Actions: `ros-tooling/setup-ros@v0.7` installs ROS 2 jazzy, a synthetic bag is generated, `apg run` writes a real RunRecord, and the workflow asserts `execution.baseline_status == "real"` before uploading the artifact).

The repository now has the benchmark-first dry-run scaffold in place, with
stricter schemas, failure-tag cross-validation, README structure checks,
failure-card stub generation, and additional CLI subcommands.

Added or confirmed:

- root docs: `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `LICENSE`, `CODEOWNERS`
- `.gitignore` and `runs/.gitignore`
- schemas:
  - `schemas/experiment.schema.json`
  - `schemas/benchmark.schema.json`
  - `schemas/benchmark_assets.schema.json`
  - `schemas/expected_failures.schema.json`
  - `schemas/failure_card.schema.json`
  - `schemas/asset.schema.json`
  - `schemas/result.schema.json`
  - `schemas/metric.schema.json`
- contracts:
  - `contracts/README.md`
  - `contracts/failure_taxonomy.yaml`
  - `contracts/topics/common_topics.md`
  - slot docs under `contracts/slots/`
- asset manifests:
  - `assets/maps/sample_map/asset.yaml`
  - `assets/rosbags/sample_lidar_localization/asset.yaml`
  - `assets/scenarios/sample_lane_change/asset.yaml`
- benchmark bundles:
  - `benchmarks/planning/lane_change_cut_in_001`
  - `benchmarks/localization/lidar_localization_replay_001`
  - `benchmarks/perception/static_obstacle_lidar_001`
  - `benchmarks/prediction/cut_in_prediction_001`
- experiment bundles:
  - `experiments/planning/autoware_baseline`
  - `experiments/planning/safe_gap_ttc_planner`
  - `experiments/localization/ndt_baseline`
  - `experiments/localization/icp_registration_toy`
  - `experiments/perception/lidar_cluster_baseline`
  - `experiments/prediction/constant_velocity_baseline`
- minimal CLI package under `tools/apg`
- runner dispatch package `tools/apg/apg/runners/`:
  - `base.py` (RunnerOutcome + ApgRunnerError)
  - `scenario_simulator_v2.py` (dry-run dispatch + execute stub)
  - `rosbag_replay.py` (dry-run dispatch + **real** `execute()` that
    resolves the bag path, runs `ros2 bag info`, and spawns
    `ros2 bag play` under the benchmark's `timeout_sec`)
  - `__init__.py` (`runner_dry_run` + `runner_execute` switches)
- preflight module `tools/apg/apg/preflight.py` (runner-aware:
  ROS_DISTRO / ros2 are required for every runner; Autoware workspace
  and `scenario_test_runner` are only required for
  `scenario_simulator_v2`; `rosbag_replay` only needs ros2)
- helper: `tools/scripts/make_sample_rosbag.py` writes a ~30 KiB
  synthetic rosbag for local real-path smoke testing
- static report generation from `RunRecord`
- tests under `tests/`
- CI workflows:
  - `.github/workflows/lint.yaml` (validate + `apg lint --allow-dry-run-baselines` gate + pytest, plus informational strict-lint job that surfaces dry-run baselines via `continue-on-error`)
  - `.github/workflows/smoke.yaml` (4-task dry-run matrix + `compare` job + `real-rosbag-replay` job that installs ROS 2 jazzy via `ros-tooling/setup-ros@v0.7`, generates a synthetic bag with `tools/scripts/make_sample_rosbag.py`, runs `apg run` without `--dry-run`, asserts the resulting RunRecord is real and `play_returncode==0`, and uploads the run as an artifact)
  - `.github/workflows/benchmark-nightly.yaml`
- placeholder docker/devcontainer/repository/docs/report files:
  - `.devcontainer/devcontainer.json`
  - `docker/Dockerfile`
  - `docker/compose.yaml`
  - `docker/entrypoint.sh`
  - `repositories/autoware-playground.repos`
  - `repositories/autoware-pinned.lock.yaml`
  - `docs/`
  - `reports/README.md`

Implemented CLI commands:

```bash
apg validate .                # warnings stay non-fatal
apg validate . --json         # machine-readable validation output
apg lint .                    # strict alias: warnings become errors
apg lint . --allow-dry-run-baselines  # CI gate: ignore dry_run baseline warning
apg list benchmarks
apg list experiments
apg run <benchmark> --experiment <experiment> --dry-run [--report]
apg report <result.json>
apg compare <left_run_dir> <right_run_dir> [--json]
apg demo lane_change_cut_in --dry-run --headless --report
apg preflight <benchmark> [--runner <type>] [--json]
apg run <benchmark> --experiment <experiment>           # non-dry-run, preflight first
```

Current dry-run behavior:

- validates benchmark and experiment manifests against typed JSON Schemas
  (`Benchmark`, `BenchmarkAssets`, `ExpectedFailures`, `MetricConfig`,
  `Experiment`, `Asset`, `RunRecord`, `FailureCard`)
- cross-validates `benchmark.failure_taxonomy` and
  `expected_failures[*].tag` against `contracts/failure_taxonomy.yaml`
  (unknown tags become errors)
- requires experiment task and benchmark task to match for any benchmark
  reference in `experiment.benchmarks.*` and at run time
- warns when an experiment or benchmark README is missing one of the
  recommended `##` section headings (warnings; `apg lint` promotes them
  to errors)
- checks required benchmark/experiment files
- checks launch and params references when present
- checks benchmark asset manifest references
- creates a run directory under `runs/`
- writes `result.json` (RunRecord-schema-conformant)
- writes a `failure_cards/<tag>.yaml` stub for every entry in `failures`
- links failure-card stubs from `report.html`
- optionally writes `report.html`
- updates `runs/latest/` (including `failure_cards/`)
- marks generated results as `execution.status: not_executed`
- marks generated results as `execution.baseline_status: dry_run` and
  warns (or errors under `apg lint`) when any baseline `result.json` is
  still labelled `dry_run`
- dispatches to a runner-specific dry-run handler based on
  `benchmark.runner.type` and records the chosen backend under
  `runtime.runner` + `runtime.runner_hints` in the RunRecord
- `apg run` without `--dry-run` runs `preflight_for_runner(...)` first
  and fails loudly with an actionable error when the environment is
  missing required pieces (no Autoware workspace, no scenario runner,
  etc.)
- for `rosbag_replay`, `apg run` (no `--dry-run`) now performs **real**
  execution: it expands `$APG_DATA`-style references in
  `benchmark.runner.rosbag`, fails fast if the bag is missing,
  spawns `ros2 bag play`, captures the exit code + elapsed time +
  bag duration/message/topic counts, and writes a real RunRecord
  with `execution.baseline_status: real` and
  `runtime.preflight` snapshotted into the record
- for `scenario_simulator_v2`, `runner_execute` still raises
  `ApgRunnerError` with next-step instructions; wiring it requires
  a pinned Autoware workspace
- uses `failures: ["sim_invalid"]` for placeholder non-executed runs

Important limitation:

The repo still does not execute Autoware, Scenario Simulator v2, rosbag replay, or ROS metrics. This is intentional for the MVP dry-run pass. Do not present current benchmark results as real benchmark evidence.

Verification completed:

```bash
rtk proxy python3 -m venv .venv
rtk proxy .venv/bin/python -m pip install -e tools/apg pytest
rtk proxy env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q
rtk proxy .venv/bin/apg validate .
rtk proxy .venv/bin/apg lint .
rtk proxy .venv/bin/apg list benchmarks
rtk proxy .venv/bin/apg list experiments
rtk proxy .venv/bin/apg demo lane_change_cut_in --dry-run --headless --report
rtk proxy .venv/bin/apg compare runs/<left> runs/<right>
rtk proxy .venv/bin/apg validate runs/latest/result.json
```

Observed verification result (after sixth pass):

```text
29 passed (incl. e2e: synthetic bag generated + ros2 bag play in test)
apg validate . → validated 37 schema-backed file(s) (4 dry_run baseline warnings)
apg lint .     → validation failed: 4 issue(s) (the 4 dry_run baseline warnings)
apg lint . --allow-dry-run-baselines → validated 37 file(s), exit 0
apg preflight benchmarks/planning/lane_change_cut_in_001 → fails on
  this machine because AUTOWARE_WORKSPACE is unset and
  scenario_test_runner is not on PATH (expected — no Autoware here yet)
apg preflight benchmarks/localization/lidar_localization_replay_001 → pass
  (rosbag_replay only requires ROS_DISTRO + ros2)
apg run benchmarks/localization/lidar_localization_replay_001
       --experiment experiments/localization/ndt_baseline --headless
  with APG_DATA=/tmp/apg_data_test pointing at a sample bag generated by
  tools/scripts/make_sample_rosbag.py → writes a REAL RunRecord with
  execution.baseline_status="real", execution.status="completed",
  metrics={rosbag_message_count: 10, rosbag_topic_count: 1, ...},
  runtime.preflight snapshot embedded
```

Note:

`python3 -m pip install ...` failed outside a virtual environment because this machine uses PEP 668 external environment management. Use `.venv` or another virtual environment for local APG development.

## 27. Next Concrete Work Items

Resume from here:

1. Clean up generated local development artifacts before commit review:
   - keep `.venv/`, `__pycache__/`, `.pytest_cache/`, `*.egg-info/`, and generated `runs/*` ignored
   - inspect `git status --short --ignored` if needed
2. Tighten schema and semantic validation: **DONE in second pass.**
   - schemas added for `BenchmarkAssets`, `ExpectedFailures`, `FailureCard`
   - failure tags validated against `contracts/failure_taxonomy.yaml`
   - benchmark and experiment tasks must match before dry-run (and inside
     `experiment.benchmarks.*` references)
   - recommended README headings checked (warnings, escalated by `apg lint`)
3. Improve APG CLI behavior: **DONE in second pass.**
   - `apg lint` added (strict validator)
   - `apg demo lane_change_cut_in --dry-run --headless --report` added
   - `apg validate --json` / `apg lint --json` emit machine-readable output
   - `apg compare` reads two `RunRecord` files and reports diffs
4. Add real runner boundaries without over-abstracting simulation: **DONE in third pass.**
   - dispatch for `scenario_simulator_v2` lives in
     `tools/apg/apg/runners/scenario_simulator_v2.py`
   - dispatch for `rosbag_replay` lives in
     `tools/apg/apg/runners/rosbag_replay.py`
   - `planning_simulator` and `awsim` keep a generic dry-run fallback
   - `apg run --dry-run` calls `runner_dry_run(...)` and records the
     chosen backend under `runtime.runner_hints`
   - unknown runner types fail loudly with `ApgRunnerError`
   - no universal simulator abstraction was introduced
5. Connect first real smoke path: **rosbag_replay path DONE in sixth pass; scenario_simulator_v2 path still TODO.**
   - `apg preflight` is runner-aware: requires ROS_DISTRO + `ros2`
     for every runner, `AUTOWARE_WORKSPACE` + `scenario_test_runner`
     only for `scenario_simulator_v2`
   - `rosbag_replay.execute(...)` now actually spawns `ros2 bag play`
     under `benchmark.runner.timeout_sec`, captures the exit code,
     elapsed wall time, bag duration / message count / topic count
     via `ros2 bag info`, and feeds them into the RunRecord
   - `run_real(...)` writes a non-dry-run `result.json` with
     `execution.dry_run=False`, `execution.baseline_status="real"`,
     `execution.status="completed"` (or `"failed"` if the player
     exits non-zero / times out), and embeds the preflight report
     under `runtime.preflight`
   - `tools/scripts/make_sample_rosbag.py` generates a ~30 KiB
     synthetic bag so the real path is reproducible without
     external data; the e2e pytest exercises it end-to-end and is
     skipped when `rosbag2_py` / `ros2` are absent
   - still TODO: wire `scenario_simulator_v2.execute(...)` against a
     pinned Autoware workspace + `scenario_test_runner` (will require
     either a Docker image or a local Autoware build)
6. Add baseline result policy: **DONE in third pass.**
   - `execution.baseline_status` field added to RunRecord schema
     (`dry_run` / `real` / `unknown`)
   - all four committed baseline `result.json` files now carry
     `baseline_status: dry_run`
   - `apg lint` surfaces every `dry_run` baseline as an error so we
     cannot accidentally treat dry-run baselines as real evidence
   - replace dry-run baselines with real baselines only when
     reproducible locally and in CI
7. First failure-card flow: **DONE in second pass.**
   - `schemas/failure_card.schema.json` added
   - `apg run --dry-run` writes `failure_cards/<tag>.yaml` stubs for each
     entry in `failures`
   - failure cards are linked from `report.html`
   - cards are mirrored into `runs/latest/failure_cards/`
8. Prepare first commit/PR:
   - review all new files
   - ensure no large data files are tracked
   - ensure generated run output is ignored
   - run tests and validation again
9. Harden CI: **DONE in fifth pass.**
   - `apg lint --allow-dry-run-baselines` integrated into `lint.yaml` as a
     gate so strict lint passes while baselines are still stubs
   - informational `strict-lint` job runs raw `apg lint .` with
     `continue-on-error: true` so dry-run baselines stay visible without
     blocking PRs; flips green once real baselines replace the stubs
   - `smoke.yaml` expanded to a 4-task matrix (planning / perception /
     localization / prediction) with per-task report artifact upload
   - `smoke.yaml` adds a `compare` job that dry-runs the planning baseline
     and experiment side-by-side and uploads `apg compare --json` output
10. Run real benchmark in CI: **DONE in seventh pass (rosbag_replay only).**
    - `smoke.yaml` adds a `real-rosbag-replay` job that installs ROS 2
      jazzy via `ros-tooling/setup-ros@v0.7`, generates a synthetic
      rosbag with `tools/scripts/make_sample_rosbag.py`, runs
      `apg run` without `--dry-run`, asserts the resulting RunRecord is
      real (`execution.baseline_status == "real"`, `dry_run == False`,
      `play_returncode == 0`, expected message count), and uploads the
      run as an artifact
    - this is the first GitHub Actions job that actually exercises a
      ROS 2 binary; scenario_simulator_v2 remains TODO and will require
      a Docker image with a pinned Autoware workspace

## 28. Implementation Notes For Next Session

Use `apply_patch` for file edits.

Because `/home/sasaki/.codex/RTK.md` says shell commands should be prefixed with `rtk`, use:

```bash
rtk proxy <command>
```

for commands where raw output matters, and:

```bash
rtk <command>
```

where summarized output is enough.

Do not use destructive git commands. The repo currently appears to be a new git repository on branch `main` with no commits, but verify that before changing assumptions.

Generated benchmark outputs should go under `runs/` and should not be committed by default.

Keep real data out of git. Use asset manifests only.

## 29. Design Bias To Preserve

When in doubt, choose the option that makes future comparisons more reliable.

Prefer:

- manifests over hidden conventions
- small benchmark cases over broad demos
- static reports over dashboards
- shadow mode over takeover mode
- failure cards over vague failure notes
- Autoware-native topics over new abstractions
- dry-run scaffolding before fake full integration
- explicit non-goals over accidental scope growth

Avoid:

- a custom simulator abstraction too early
- a generic plugin system too early
- custom ROS messages
- large binary assets
- implementation-only PRs
- changing upstream Autoware
- claiming real benchmark support before real runner integration exists

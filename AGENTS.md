# autoware-playground agent rules

## Prime directive

This repository is an Autoware experimentation overlay.
Do not create a mini Autoware.
Do not redefine Autoware messages.
Do not edit upstream Autoware repositories.

## Required files for a new experiment

Every experiment must include:

- `README.md`
- `experiment.yaml`
- launch file or explicit reason why not needed
- `params/default.yaml` if parameters exist
- at least one benchmark result or smoke benchmark
- known limitations
- failure analysis section

## Required files for a new benchmark

Every benchmark must include:

- `benchmark.yaml`
- `metrics.yaml`
- `assets.yaml`
- `README.md`
- `expected_failures.yaml`
- baseline result if runnable

## Preferred implementation style

- Small files.
- Explicit launch, remap, and params.
- No hidden downloads.
- No global refactor.
- Shadow mode before takeover mode.
- Add tests for schema and CLI behavior.
- Keep benchmark reproducible.

## Forbidden by default

- Modifying Autoware source directly.
- Adding large binary assets to git.
- Introducing a new simulator abstraction.
- Adding custom ROS messages unless approved.
- Changing benchmark thresholds without explaining why.

## Experiment README order

Use this order so AI agents and human reviewers can make small, scoped PRs:

1. What this method does
2. Paper summary
3. Autoware slot
4. Inputs and outputs
5. How to run smoke benchmark
6. Expected result
7. Known failure modes
8. Files you are allowed to edit

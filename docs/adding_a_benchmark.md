# Adding A Benchmark

Create benchmark cases under `benchmarks/<task>/<case_name>/`.

Every benchmark must include:

- `README.md`
- `benchmark.yaml`
- `metrics.yaml`
- `assets.yaml`
- `expected_failures.yaml`
- a baseline result when runnable

Reference maps, rosbags, scenarios, models, and datasets through asset manifests. Do not commit large data files.

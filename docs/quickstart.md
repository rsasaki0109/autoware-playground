# Quickstart

Install the MVP CLI:

```bash
python -m pip install -e tools/apg
```

Validate the repository:

```bash
apg validate .
```

Run the planning dry-run smoke benchmark:

```bash
apg run benchmarks/planning/lane_change_cut_in_001 \
  --experiment experiments/planning/safe_gap_ttc_planner \
  --headless \
  --dry-run \
  --report
```

Open `runs/latest/report.html` to inspect the generated static report.

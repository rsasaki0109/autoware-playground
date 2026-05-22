# Contracts

Contracts describe how experiments connect to existing Autoware interfaces. They are not a plugin SDK and they do not redefine messages.

Use these files to decide:

- which Autoware topics an experiment may read
- which candidate topic it should publish in shadow mode
- which Autoware topic may be remapped in takeover mode
- which metrics are expected for a benchmark

Initial slots:

- `localization.pose_estimator`
- `perception.objects3d`
- `perception.occupancy_grid`
- `prediction.objects`
- `planning.behavior`
- `planning.motion`
- `planning.trajectory`

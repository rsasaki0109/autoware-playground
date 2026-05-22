# Reproducibility

Every run should record:

- autoware-playground commit
- Autoware lock reference
- ROS distribution
- container digest when available
- asset checksums
- benchmark and experiment manifests
- metrics
- failures
- reproduce command

MVP dry-runs write `execution.status: not_executed` so placeholder runs are not confused with real benchmark evidence.

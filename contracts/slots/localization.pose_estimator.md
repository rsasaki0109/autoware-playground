# Slot: localization.pose_estimator

Purpose: compare localization methods such as NDT, ICP, LIO, and GNSS fusion.

MVP modes: `shadow`, `takeover`, `offline_replay`

Typical inputs:

| Topic | Type |
|---|---|
| `/sensing/lidar/concatenated/pointcloud` | `sensor_msgs/msg/PointCloud2` |
| `/initialpose` | `geometry_msgs/msg/PoseWithCovarianceStamped` |
| map asset | external asset manifest |

Shadow output:

| Topic | Type |
|---|---|
| `/awpg/experiments/<name>/pose` | `geometry_msgs/msg/PoseWithCovarianceStamped` |

Takeover output:

| Topic | Type |
|---|---|
| `/localization/pose_with_covariance` | `geometry_msgs/msg/PoseWithCovarianceStamped` |

Expected diagnostics include ATE, RPE, convergence time, pose jumps, output availability, and CPU time.

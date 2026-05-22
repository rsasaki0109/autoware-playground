# Slot: perception.objects3d

Purpose: compare 3D object detection, clustering, and fusion methods.

MVP mode: `shadow`

Typical inputs:

| Topic | Type |
|---|---|
| `/sensing/lidar/concatenated/pointcloud` | `sensor_msgs/msg/PointCloud2` |
| `/localization/kinematic_state` | `nav_msgs/msg/Odometry` |

Shadow output:

| Topic | Type |
|---|---|
| `/awpg/experiments/<name>/objects` | `autoware_perception_msgs/msg/PredictedObjects` |

Expected diagnostics include detection availability, latency, object center error, missed detections, and false positives in the drivable area.

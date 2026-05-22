# Slot: perception.occupancy_grid

Purpose: compare freespace and occupancy-grid methods before they are used by planning.

MVP mode: `shadow`

Typical inputs:

| Topic | Type |
|---|---|
| `/sensing/lidar/concatenated/pointcloud` | `sensor_msgs/msg/PointCloud2` |
| `/localization/kinematic_state` | `nav_msgs/msg/Odometry` |

Shadow output:

| Topic | Type |
|---|---|
| `/awpg/experiments/<name>/occupancy_grid` | `nav_msgs/msg/OccupancyGrid` |

Expected diagnostics include occupancy IoU, freespace precision, freespace recall, and latency.

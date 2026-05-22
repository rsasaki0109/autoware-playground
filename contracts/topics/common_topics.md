# Common Autoware Topics

These topics are examples used by the initial manifests. Benchmark-specific README files may narrow or extend them.

| Purpose | Topic | Type |
|---|---|---|
| Baseline trajectory | `/planning/scenario_planning/trajectory` | `autoware_planning_msgs/msg/Trajectory` |
| Predicted objects | `/perception/object_recognition/objects` | `autoware_perception_msgs/msg/PredictedObjects` |
| Ego odometry | `/localization/kinematic_state` | `nav_msgs/msg/Odometry` |
| Point cloud | `/sensing/lidar/concatenated/pointcloud` | `sensor_msgs/msg/PointCloud2` |
| Candidate trajectory | `/awpg/experiments/<name>/trajectory` | `autoware_planning_msgs/msg/Trajectory` |
| Candidate pose | `/awpg/experiments/<name>/pose` | `geometry_msgs/msg/PoseWithCovarianceStamped` |
| Candidate objects | `/awpg/experiments/<name>/objects` | `autoware_perception_msgs/msg/PredictedObjects` |

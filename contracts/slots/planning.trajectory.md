# Slot: planning.trajectory

Purpose: compare end-to-end, learned, VLM, or world-model planners as candidate trajectory producers.

MVP mode: `shadow`

Typical inputs:

| Topic | Type |
|---|---|
| `/planning/scenario_planning/trajectory` | `autoware_planning_msgs/msg/Trajectory` |
| `/perception/object_recognition/objects` | `autoware_perception_msgs/msg/PredictedObjects` |
| `/localization/kinematic_state` | `nav_msgs/msg/Odometry` |
| camera or sensor topics | benchmark-specific |

Shadow output:

| Topic | Type |
|---|---|
| `/awpg/experiments/<name>/trajectory` | `autoware_planning_msgs/msg/Trajectory` |

Optional explanation output:

| Topic | Type |
|---|---|
| `/awpg/experiments/<name>/explanation` | `std_msgs/msg/String` |

Expected diagnostics should compare candidate trajectory quality first. Ego takeover is out of scope for MVP unless a benchmark explicitly allows it.

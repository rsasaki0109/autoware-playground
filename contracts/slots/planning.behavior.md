# Slot: planning.behavior

Purpose: compare behavior-level decisions such as lane change, avoidance, yield, stop, and pull over.

MVP modes: `shadow`, `takeover`

Typical inputs:

| Topic | Type |
|---|---|
| `/perception/object_recognition/objects` | `autoware_perception_msgs/msg/PredictedObjects` |
| `/localization/kinematic_state` | `nav_msgs/msg/Odometry` |
| `/planning/mission_planning/route` | `autoware_planning_msgs/msg/LaneletRoute` |

Shadow output:

| Topic | Type |
|---|---|
| `/awpg/experiments/<name>/behavior_path` | `autoware_internal_planning_msgs/msg/PathWithLaneId` |

Expected diagnostics include route completion, deadlock duration, rule violations, and intent oscillation.

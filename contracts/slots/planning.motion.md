# Slot: planning.motion

Purpose: compare motion planning and trajectory optimization methods.

MVP modes: `shadow`, `takeover`

Typical inputs:

| Topic | Type |
|---|---|
| `/planning/scenario_planning/trajectory` | `autoware_planning_msgs/msg/Trajectory` |
| `/perception/object_recognition/objects` | `autoware_perception_msgs/msg/PredictedObjects` |
| `/localization/kinematic_state` | `nav_msgs/msg/Odometry` |

Shadow output:

| Topic | Type |
|---|---|
| `/awpg/experiments/<name>/trajectory` | `autoware_planning_msgs/msg/Trajectory` |

Takeover output:

| Topic | Type |
|---|---|
| `/planning/scenario_planning/trajectory` | `autoware_planning_msgs/msg/Trajectory` |

Expected diagnostics include collision, route completion, minimum TTC, maximum jerk, lateral acceleration, trajectory stability, and planner oscillation.

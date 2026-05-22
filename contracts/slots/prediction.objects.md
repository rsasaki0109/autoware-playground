# Slot: prediction.objects

Purpose: compare object trajectory prediction methods.

MVP mode: `shadow`

Typical inputs:

| Topic | Type |
|---|---|
| `/perception/object_recognition/objects` | `autoware_perception_msgs/msg/DetectedObjects` |
| `/localization/kinematic_state` | `nav_msgs/msg/Odometry` |

Shadow output:

| Topic | Type |
|---|---|
| `/awpg/experiments/<name>/predicted_objects` | `autoware_perception_msgs/msg/PredictedObjects` |

Expected diagnostics include minADE, minFDE, prediction topic availability, and downstream planner TTC with predicted actors.

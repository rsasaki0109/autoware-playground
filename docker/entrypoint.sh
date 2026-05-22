#!/usr/bin/env bash
set -euo pipefail

if [[ -f /opt/ros/${ROS_DISTRO:-humble}/setup.bash ]]; then
  source "/opt/ros/${ROS_DISTRO:-humble}/setup.bash"
fi

exec "$@"

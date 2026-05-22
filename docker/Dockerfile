ARG ROS_DISTRO=humble
FROM ros:${ROS_DISTRO}-ros-base

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    git \
    python3-pip \
    python3-venv \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/autoware-playground
COPY docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]

# ROS 2 Jazzy + MoveIt 2 + xArm/Lite 6 + OAK-D + Amiga control
# Target: Jetson Orin NX (arm64), Ubuntu 24.04 / JetPack 7.2
FROM ros:jazzy-ros-base

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]

# --- Binary packages from the ROS apt repository ---
RUN apt-get update && apt-get install -y --no-install-recommends \
      ros-jazzy-moveit \
      ros-jazzy-depthai-ros \
      ros-jazzy-rviz2 \
      ros-jazzy-xacro \
      ros-jazzy-robot-state-publisher \
      ros-jazzy-joint-state-publisher-gui \
      ros-jazzy-ros2-control \
      ros-jazzy-ros2-controllers \
      ros-jazzy-joy \
      ros-jazzy-teleop-twist-joy \
      ros-jazzy-teleop-twist-keyboard \
      git \
      python3-colcon-common-extensions \
      python3-rosdep \
      python3-vcstool \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ros2_ws

# --- xArm / Lite 6 driver + MoveIt config (source, jazzy branch) ---
RUN git clone -b jazzy --recursive --depth 1 \
      https://github.com/xArm-Developer/xarm_ros2.git src/xarm_ros2

# --- micro-ROS agent for the Amiga Portenta (no apt package for Jazzy) ---
RUN git clone -b jazzy https://github.com/micro-ROS/micro-ROS-Agent.git src/micro-ROS-Agent \
 && git -C src/micro-ROS-Agent checkout 7c932329ad5591ef23942ef1962534258c16b000 \
 && git clone -b jazzy https://github.com/micro-ROS/micro_ros_msgs.git src/micro_ros_msgs \
 && git -C src/micro_ros_msgs checkout b1ef85201e5545d3e07b73f4628bb15836062573

# --- Amiga control (external repo) ---
# Pass at build time: --build-arg AMIGA_REPO=<git-url>
# Empty = skip.
ARG AMIGA_REPO=""
ARG AMIGA_BRANCH="main"
RUN if [ -n "$AMIGA_REPO" ]; then \
      git clone -b "$AMIGA_BRANCH" --depth 1 "$AMIGA_REPO" src/amiga_control ; \
    fi

# --- Remaining dependencies via rosdep ---
RUN apt-get update && rosdep update \
    && rosdep install --from-paths src --ignore-src -r -y \
    && rm -rf /var/lib/apt/lists/*

# --- Build ---
# Limit parallel jobs: the Orin NX runs out of memory otherwise.
ENV MAKEFLAGS="-j2"
RUN source /opt/ros/jazzy/setup.bash \
    && colcon build --symlink-install --parallel-workers 2 \
         --cmake-args -DCMAKE_BUILD_TYPE=Release

# --- Amiga robot model (pinned tag) ---
# Own layer after the big build, so bumping the tag does not rebuild xarm.
RUN git clone -b v0.5.1 --depth 1 https://github.com/Avans-Robotics/amiga_description.git src/amiga_description \
 && source /opt/ros/jazzy/setup.bash \
 && colcon build --symlink-install --packages-select amiga_description

# --- Source the workspace automatically ---
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc \
 && echo "source /ros2_ws/install/setup.bash" >> /root/.bashrc
COPY ros_entrypoint.sh /ros_entrypoint.sh
RUN chmod +x /ros_entrypoint.sh
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]

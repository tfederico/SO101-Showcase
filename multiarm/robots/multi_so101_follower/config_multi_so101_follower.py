#!/usr/bin/env python

# Copyright 2025 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dataclasses import dataclass, field

from lerobot.cameras import CameraConfig

from lerobot.robots.config import RobotConfig


@RobotConfig.register_subclass("multi_so101_follower")
@dataclass
class MultiSO101FollowerConfig(RobotConfig):
    """
    Configuration for multiple SO-101 Follower arms.
    
    Example:
        config = MultiSO101FollowerConfig(
            arm_ports={"left": "/dev/tty.usbmodem1", "right": "/dev/tty.usbmodem2"},
            arm_disable_torque_on_disconnect={"left": True, "right": True},
            arm_use_degrees={"left": False, "right": False}
        )
    """
    
    arm_ports: dict[str, str] = field(default_factory=dict)
    
    # Optional - if not specified for an arm, uses default values
    arm_disable_torque_on_disconnect: dict[str, bool] = field(default_factory=dict)
    arm_max_relative_target: dict[str, float | dict[str, float] | None] = field(default_factory=dict)
    arm_use_degrees: dict[str, bool] = field(default_factory=dict)
    
    # Cameras (shared between all arms)
    cameras: dict[str, CameraConfig] = field(default_factory=dict)
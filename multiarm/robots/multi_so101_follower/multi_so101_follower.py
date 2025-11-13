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

import logging
import time
from functools import cached_property
from typing import Any

from lerobot.cameras.utils import make_cameras_from_configs
from lerobot.robots.so101_follower import SO101Follower
from lerobot.robots.so101_follower.config_so101_follower import SO101FollowerConfig

from lerobot.robots.robot import Robot
from .config_multi_so101_follower import MultiSO101FollowerConfig

logger = logging.getLogger(__name__)


class MultiSO101Follower(Robot):
    """
    Implementation supporting multiple SO-101 Follower Arms.
    Based on src/lerobot/robots/bi_so100_follower/bi_so100_follower.py
    [SO-101 Follower Arms](https://github.com/TheRobotStudio/SO-ARM100) designed by TheRobotStudio
    
    Supports an arbitrary number of arms with configurable names and ports.
    """

    config_class = MultiSO101FollowerConfig
    name = "multi_so101_follower"

    def __init__(self, config: MultiSO101FollowerConfig):
        super().__init__(config)
        self.config = config

        # Initialize arms based on configuration
        self.arms: dict[str, SO101Follower] = {}
        
        for arm_name, port in config.arm_ports.items():
            arm_config = SO101FollowerConfig(
                id=f"{config.id}_{arm_name}" if config.id else None,
                calibration_dir=config.calibration_dir,
                port=port,
                disable_torque_on_disconnect=config.arm_disable_torque_on_disconnect.get(arm_name, True),
                max_relative_target=config.arm_max_relative_target.get(arm_name, None),
                use_degrees=config.arm_use_degrees.get(arm_name, True),
                cameras={},
            )
            self.arms[arm_name] = SO101Follower(arm_config)
        
        self.cameras = make_cameras_from_configs(config.cameras)

    @property
    def _motors_ft(self) -> dict[str, type]:
        features = {}
        for arm_name, arm in self.arms.items():
            for motor in arm.bus.motors:
                features[f"{arm_name}_{motor}.pos"] = float
        return features

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        return {
            cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3) for cam in self.cameras
        }

    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        return {**self._motors_ft, **self._cameras_ft}

    @cached_property
    def action_features(self) -> dict[str, type]:
        return self._motors_ft

    @property
    def is_connected(self) -> bool:
        return (
            all(arm.bus.is_connected for arm in self.arms.values())
            and all(cam.is_connected for cam in self.cameras.values())
        )

    def connect(self, calibrate: bool = True) -> None:
        for arm in self.arms.values():
            arm.connect(calibrate)

        for cam in self.cameras.values():
            cam.connect()

    @property
    def is_calibrated(self) -> bool:
        return all(arm.is_calibrated for arm in self.arms.values())

    def calibrate(self) -> None:
        for arm in self.arms.values():
            arm.calibrate()

    def configure(self) -> None:
        for arm in self.arms.values():
            arm.configure()

    def setup_motors(self) -> None:
        for arm in self.arms.values():
            arm.setup_motors()

    def get_observation(self) -> dict[str, Any]:
        obs_dict = {}

        # Get observations from all arms
        for arm_name, arm in self.arms.items():
            arm_obs = arm.get_observation()
            obs_dict.update({f"{arm_name}_{key}": value for key, value in arm_obs.items()})

        # Get camera observations
        for cam_key, cam in self.cameras.items():
            start = time.perf_counter()
            obs_dict[cam_key] = cam.async_read()
            dt_ms = (time.perf_counter() - start) * 1e3
            logger.debug(f"{self} read {cam_key}: {dt_ms:.1f}ms")

        return obs_dict

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        result = {}
        
        # Group actions by arm prefix
        for arm_name, arm in self.arms.items():
            prefix = f"{arm_name}_"
            # Extract actions for this arm
            arm_action = {
                key.removeprefix(prefix): value 
                for key, value in action.items() 
                if key.startswith(prefix)
            }
            
            if arm_action:
                send_action_result = arm.send_action(arm_action)
                # Add prefix back to results
                result.update({f"{arm_name}_{key}": value for key, value in send_action_result.items()})

        return result

    def disconnect(self):
        for arm in self.arms.values():
            arm.disconnect()

        for cam in self.cameras.values():
            cam.disconnect()
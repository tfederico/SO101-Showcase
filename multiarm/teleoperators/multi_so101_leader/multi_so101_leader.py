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
from functools import cached_property

from lerobot.teleoperators.so101_leader.config_so101_leader import SO101LeaderConfig
from lerobot.teleoperators.so101_leader.so101_leader import SO101Leader

from lerobot.teleoperators.teleoperator import Teleoperator
from .config_multi_so101_leader import MultiSO101LeaderConfig

logger = logging.getLogger(__name__)


class MultiSO101Leader(Teleoperator):
    """
    Implementation supporting multiple SO-101 Leader Arms.
    Based on src/lerobot/teleoperators/bi_so100_leader/bi_so100_leader.py
    [SO-101 Leader Arms](https://github.com/TheRobotStudio/SO-ARM100) designed by TheRobotStudio
    
    Supports an arbitrary number of arms with configurable names and ports.
    """

    config_class = MultiSO101LeaderConfig
    name = "multi_so101_leader"

    def __init__(self, config: MultiSO101LeaderConfig):
        super().__init__(config)
        self.config = config

        # Initialize arms based on configuration
        self.arms: dict[str, SO101Leader] = {}
        
        for arm_name, arm_port in config.arms.items():
            arm_config = SO101LeaderConfig(
                id=f"{config.id}_{arm_name}" if config.id else None,
                calibration_dir=config.calibration_dir,
                port=arm_port,
            )
            self.arms[arm_name] = SO101Leader(arm_config)

    @cached_property
    def action_features(self) -> dict[str, type]:
        features = {}
        for arm_name, arm in self.arms.items():
            for motor in arm.bus.motors:
                features[f"{arm_name}_{motor}.pos"] = float
        return features

    @cached_property
    def feedback_features(self) -> dict[str, type]:
        return {}

    @property
    def is_connected(self) -> bool:
        return all(arm.is_connected for arm in self.arms.values())

    def connect(self, calibrate: bool = True) -> None:
        for arm in self.arms.values():
            arm.connect(calibrate)

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

    def get_action(self) -> dict[str, float]:
        action_dict = {}
        
        for arm_name, arm in self.arms.items():
            arm_action = arm.get_action()
            # Add arm name prefix to each action key
            action_dict.update({f"{arm_name}_{key}": value for key, value in arm_action.items()})
        
        return action_dict

    def send_feedback(self, feedback: dict[str, float]) -> None:
        # Group feedback by arm prefix
        arm_feedbacks = {arm_name: {} for arm_name in self.arms.keys()}
        
        for key, value in feedback.items():
            # Find which arm this feedback belongs to
            for arm_name in self.arms.keys():
                prefix = f"{arm_name}_"
                if key.startswith(prefix):
                    # Remove prefix and add to corresponding arm's feedback
                    arm_feedbacks[arm_name][key.removeprefix(prefix)] = value
                    break
        
        # Send feedback to each arm that has feedback data
        for arm_name, arm_feedback in arm_feedbacks.items():
            if arm_feedback:
                self.arms[arm_name].send_feedback(arm_feedback)

    def disconnect(self) -> None:
        for arm in self.arms.values():
            arm.disconnect()
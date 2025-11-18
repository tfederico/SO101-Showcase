"""
Dataset recording script for multi-arm SO101 robotic setup.

This script records demonstration episodes of multiple robot arms performing tasks under human
teleoperation. It captures robot states, actions, and camera observations, storing
them in a LeRobot dataset format suitable for imitation learning training.

The recording process includes:
- Multiple episodes with configurable duration
- Reset periods between episodes
- Keyboard controls for episode management (stop, re-record)
- Real-time visualization via Rerun
- Automatic upload to HuggingFace Hub

Usage:
    python record_dataset_multi.py

Controls:
    Press designated keys during recording to stop or re-record episodes
    (specific keys configured in keyboard listener)
"""
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.cameras.realsense.configuration_realsense import RealSenseCameraConfig
from lerobot.cameras.configs import ColorMode, Cv2Rotation
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from multiarm.robots.multi_so101_follower import MultiSO101Follower, MultiSO101FollowerConfig
from multiarm.teleoperators.multi_so101_leader import MultiSO101Leader, MultiSO101LeaderConfig
from lerobot.processor import make_default_processors
from lerobot.scripts.lerobot_record import record_loop
import pathlib
from lerobot.utils.control_utils import init_keyboard_listener
from lerobot.utils.utils import init_logging, log_say
from lerobot.utils.visualization_utils import init_rerun
from lerobot.datasets.pipeline_features import (
    aggregate_pipeline_dataset_features,
    create_initial_features,
)
from lerobot.datasets.utils import combine_feature_dicts


# ============================================================================
# CONFIGURATION - Change these settings
# ============================================================================

# Dataset settings
REPO_ID = "your_username/my_multi_arm_dataset"
TASK = "Multi-arm pick and place task"
NUM_EPISODES = 1
FPS = 15

# Hardware ports for follower arms
ARM_PORTS = {
    "left": "/dev/ttyACM1",
    "right": "/dev/ttyACM2",
    # Add more arms as needed:
    # "center": "/dev/tty.usbmodem58760434473",
}

# Hardware ports for leader arms (teleoperation)
LEADER_PORTS = {
    "left": "/dev/ttyACM0",
    "right": "/dev/ttyACM3",
    # Add more arms matching the follower setup:
    # "center": "/dev/tty.usbmodem585A0077583",
}

# Camera settings (camera_name: index)
CAMERAS = {
    "wrist_left": 2,
    "wrist_right": 4,
    "realsense_top": "243322073128",  # RealSense camera serial number
}

# Recording duration (seconds)
EPISODE_TIME = 60
RESET_TIME = 10
CALIB_DIR = pathlib.Path("calibration")


# ============================================================================
# MAIN SCRIPT
# ============================================================================

def main():
    init_logging()
    init_rerun(session_name="recording")
    
    # Setup cameras (use different config for realsense cameras)
    cameras = {}
    for name, idx in CAMERAS.items():
        if "realsense" in name.lower():
            # Realsense: higher resolution
            cameras[name] = RealSenseCameraConfig( # Configure the RealSense camera with desired parameters
                serial_number_or_name=idx,  # Unique serial number of the RealSense camera
                fps=FPS,                                 # Frame rate: 15 frames per second
                width=640,                              # Image width in pixels
                height=480,                             # Image height in pixels
                color_mode=ColorMode.RGB,               # Color format: RGB (Red-Green-Blue)
                use_depth=False,                         # Enable depth sensing capability
                rotation=Cv2Rotation.NO_ROTATION        # No image rotation applied
            )
        else:
            # Default cameras
            cameras[name] = OpenCVCameraConfig(index_or_path=idx, width=640, height=480, fps=FPS)
    
    # Create multi-arm robot and teleop
    robot = MultiSO101Follower(MultiSO101FollowerConfig(
        arm_ports=ARM_PORTS,
        # Optional: configure per-arm settings
        arm_disable_torque_on_disconnect={arm: True for arm in ARM_PORTS},
        arm_use_degrees={arm: False for arm in ARM_PORTS},
        # Optional: configure max relative targets per arm if needed
        # arm_max_relative_target={arm: None for arm in ARM_PORTS},
        id="multi_follower",
        cameras=cameras,
        calibration_dir=CALIB_DIR,
    ))
    
    teleop = MultiSO101Leader(MultiSO101LeaderConfig(
        arms=LEADER_PORTS,
        id="multi_leader",
        calibration_dir=CALIB_DIR,
    ))
    
    # Create processors
    teleop_proc, robot_proc, obs_proc = make_default_processors()
    
    # Build dataset features
    features = combine_feature_dicts(
        aggregate_pipeline_dataset_features(
            pipeline=teleop_proc,
            initial_features=create_initial_features(action=robot.action_features),
            use_videos=True,
        ),
        aggregate_pipeline_dataset_features(
            pipeline=obs_proc,
            initial_features=create_initial_features(observation=robot.observation_features),
            use_videos=True,
        ),
    )
    
    # Create dataset
    dataset = LeRobotDataset.create(
        REPO_ID,
        fps=FPS,
        root="./datasets/trial_multi_arm_1",
        robot_type=robot.name,
        features=features,
        use_videos=True,
        image_writer_threads=4 * len(cameras),
    )
    
    # Setup keyboard controls
    _, events = init_keyboard_listener()
    
    # Connect hardware
    robot.connect()
    teleop.connect()
    log_say("Ready to record")
    
    # Record episodes
    episode = 0
    while episode < NUM_EPISODES and not events["stop_recording"]:
        log_say(f"Recording episode {episode + 1}")
        
        # Record
        record_loop(
            robot=robot,
            events=events,
            fps=FPS,
            teleop_action_processor=teleop_proc,
            robot_action_processor=robot_proc,
            robot_observation_processor=obs_proc,
            dataset=dataset,
            teleop=teleop,
            control_time_s=EPISODE_TIME,
            single_task=TASK,
            display_data=True,
        )
        
        # Reset environment (no dataset recording during reset)
        if not events["stop_recording"] and (episode < NUM_EPISODES - 1 or events["rerecord_episode"]):
            log_say("Reset environment")
            record_loop(
                robot=robot,
                events=events,
                fps=FPS,
                teleop_action_processor=teleop_proc,
                robot_action_processor=robot_proc,
                robot_observation_processor=obs_proc,
                teleop=teleop,
                control_time_s=RESET_TIME,
                single_task=TASK,
                display_data=True,
            )
        
        # Handle re-record
        if events["rerecord_episode"]:
            log_say("Re-recording")
            events["rerecord_episode"] = False
            events["exit_early"] = False
            dataset.clear_episode_buffer()
            continue
        
        # Save episode
        dataset.save_episode()
        episode += 1
    
    # Cleanup
    log_say("Done recording")
    robot.disconnect()
    teleop.disconnect()
    
    # Optional: upload to HuggingFace
    # dataset.push_to_hub()
    
    print(f"\nRecorded {dataset.num_episodes} episodes")
    print(f"Dataset saved to: {dataset.root}")


if __name__ == "__main__":
    main()
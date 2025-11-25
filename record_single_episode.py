"""
Single episode recording script for multi-arm SO101 robotic setup.

This script records a single demonstration episode that can later be merged
with other single episodes to create a larger dataset. It's useful for:
- Incremental data collection
- Recording episodes at different times
- Building datasets gradually without long recording sessions

The recording process includes:
- One episode per run
- Configurable episode duration
- Real-time visualization via Rerun
- Automatic dataset naming with timestamp

Usage:
    python record_single_episode.py

Controls:
    Press designated keys during recording to stop or re-record the episode
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
from datetime import datetime
from lerobot.utils.control_utils import init_keyboard_listener
from lerobot.utils.utils import init_logging, log_say
from lerobot.utils.visualization_utils import init_rerun
from lerobot.datasets.pipeline_features import (
    aggregate_pipeline_dataset_features,
    create_initial_features,
)
from lerobot.datasets.utils import combine_feature_dicts
import json


# ============================================================================
# CONFIGURATION - Change these settings
# ============================================================================

# Dataset settings
BASE_REPO_ID = "your_username/multi_arm_episode"  # Will append timestamp
TASK = "Multi-arm pick and place task"
FPS = 30

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

# Camera settings (camera_name: index) - read from configs.json if available

CAMERAS = {}


with open("configs.json") as f:
    cfg = json.load(f)
cams = cfg.get("cameras", {})
for group in ("wrist", "top"):
    for name, val in cams.get(group, {}).items():
        key = f"{group}_{name}" if group == "wrist" else f"realsense_{name}"
        CAMERAS[key] = val

# Recording duration (seconds)
EPISODE_TIME = 120
CALIB_DIR = pathlib.Path("calibration")


# ============================================================================
# MAIN SCRIPT
# ============================================================================

def main():
    init_logging()
    init_rerun(session_name="recording_single")
    
    # Generate unique dataset name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    repo_id = f"{BASE_REPO_ID}_{timestamp}"
    dataset_root = f"./datasets/single_episodes/episode_{timestamp}"
    
    log_say(f"Recording single episode to: {repo_id}")
    
    # Setup cameras (use different config for realsense cameras)
    cameras = {}
    for name, idx in CAMERAS.items():
        if "realsense" in name.lower():
            # Realsense: higher resolution
            cameras[name] = RealSenseCameraConfig(
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
        repo_id,
        fps=FPS,
        root=dataset_root,
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
    log_say("Ready to record single episode")
    
    # Record single episode (with re-record capability)
    while True:
        log_say("Recording episode")
        
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
        
        # Handle stop or re-record
        if events["stop_recording"]:
            log_say("Recording stopped")
            break
        
        if events["rerecord_episode"]:
            log_say("Re-recording episode")
            events["rerecord_episode"] = False
            events["exit_early"] = False
            dataset.clear_episode_buffer()
            continue
        
        # Save episode and exit
        dataset.save_episode()
        break
    
    # Cleanup
    log_say("Done recording")
    robot.disconnect()
    teleop.disconnect()
    
    # Print summary
    if dataset.num_episodes > 0:
        print(f"\n✓ Successfully recorded 1 episode")
        print(f"  Repository ID: {repo_id}")
        print(f"  Dataset saved to: {dataset.root}")
        print(f"\nTo merge this with other episodes, use merge_single_episodes.py")
    else:
        print("\n✗ No episode was saved")


if __name__ == "__main__":
    main()

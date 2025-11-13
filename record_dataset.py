"""
Simple Robot Recording Script

Records robot demonstrations with teleoperation.
Just set your config and run!
"""

from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig
from lerobot.teleoperators.so101_leader import SO101Leader, SO101LeaderConfig
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
REPO_ID = "your_username/my_dataset"
TASK = "Pick and place the object"
NUM_EPISODES = 5
FPS = 30

# Hardware ports
ROBOT_PORT = "/dev/ttyACM1"
TELEOP_PORT = "/dev/ttyACM0"

# Camera settings (camera_name: index)
CAMERAS = {
    "wrist": 2,
    # "workspace": 1,  # Add more cameras if needed
}

# Recording duration (seconds)
EPISODE_TIME = 60
RESET_TIME = 15
CALIB_DIR = pathlib.Path("calibration")


# ============================================================================
# MAIN SCRIPT
# ============================================================================

def main():
    init_logging()
    init_rerun(session_name="recording")
    
    # Setup cameras
    cameras = {
        name: OpenCVCameraConfig(index_or_path=idx, width=640, height=480, fps=FPS)
        for name, idx in CAMERAS.items()
    }
    
    # Create robot and teleop
    robot = SO101Follower(SO101FollowerConfig(
        port=ROBOT_PORT,
        id="B",
        cameras=cameras,
        calibration_dir=CALIB_DIR,
    ))
    
    teleop = SO101Leader(SO101LeaderConfig(
        port=TELEOP_PORT,
        id="A",
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
        root="./datasets",
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
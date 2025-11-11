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
    python record_dataset.py

Controls:
    Press designated keys during recording to stop or re-record episodes
    (specific keys configured in keyboard listener)
"""
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.utils import hw_to_dataset_features
from multiarm.robots.multi_so101_follower import MultiSO101Follower, MultiSO101FollowerConfig
from multiarm.teleoperators.multi_so101_leader import MultiSO101Leader, MultiSO101LeaderConfig
from lerobot.utils.control_utils import init_keyboard_listener
from lerobot.utils.utils import log_say
from lerobot.utils.visualization_utils import init_rerun
from lerobot.scripts.lerobot_record import record_loop

# Recording configuration parameters
NUM_EPISODES = 5                    # Total number of episodes to record
FPS = 30                            # Frames per second for data capture
EPISODE_TIME_SEC = 60               # Maximum duration of each episode in seconds
RESET_TIME_SEC = 10                 # Time allowed for environment reset between episodes
TASK_DESCRIPTION = "My task description"  # Description of the task being demonstrated

# Create the robot and teleoperator configurations
# Configure multiple cameras:
# - 1 top view camera (global view of workspace)
# - 2 wrist cameras (one per arm for close-up views)
camera_config = {
    "top": OpenCVCameraConfig(index_or_path=0, width=640, height=480, fps=FPS),
    "wrist_left": OpenCVCameraConfig(index_or_path=2, width=640, height=480, fps=FPS),
    "wrist_right": OpenCVCameraConfig(index_or_path=4, width=640, height=480, fps=FPS),
}

# Configure the follower robots (the arms that perform the task)
# Each arm needs: port, and optional settings (disable_torque, max_relative_target, use_degrees)
robot_config = MultiSO101FollowerConfig(
    arm_ports={
        "left": "/dev/tty.usbmodem58760434471",
        "right": "/dev/tty.usbmodem58760434472",
        # Add more arms as needed:
        # "center": "/dev/tty.usbmodem58760434473",
    },
    # Optional: configure per-arm settings
    arm_disable_torque_on_disconnect={
        "left": True,
        "right": True,
    },
    arm_use_degrees={
        "left": False,
        "right": False,
    },
    # Optional: configure max relative targets per arm if needed
    # arm_max_relative_target={
    #     "left": None,
    #     "right": None,
    # },
    id="my_awesome_multi_follower",
    cameras=camera_config  # Shared cameras across all arms
)

# Configure the leader arms (used for teleoperation control)
teleop_config = MultiSO101LeaderConfig(
    arms={
        "left": "/dev/tty.usbmodem585A0077581",
        "right": "/dev/tty.usbmodem585A0077582",
        # Add more arms matching the follower setup:
        # "center": "/dev/tty.usbmodem585A0077583",
    },
    id="my_awesome_multi_leader"
)

# Initialize the robot and teleoperator instances
robot = MultiSO101Follower(robot_config)
teleop = MultiSO101Leader(teleop_config)

# Configure the dataset features
# Convert robot hardware features to dataset-compatible format
action_features = hw_to_dataset_features(robot.action_features, "action")
obs_features = hw_to_dataset_features(robot.observation_features, "observation")
dataset_features = {**action_features, **obs_features}

# Create the dataset with specified configuration
dataset = LeRobotDataset.create(
    repo_id="<hf_username>/<dataset_repo_id>",  # HuggingFace repository ID (update with your username)
    fps=FPS,                                     # Recording frame rate
    features=dataset_features,                   # Data schema for actions and observations
    robot_type=robot.name,                       # Robot type identifier
    root="./recorded_dataset",                   # Local directory to store dataset
    use_videos=True,                             # Save camera data as videos (compressed)
    image_writer_threads=4,                      # Number of threads for parallel image writing
)

# Initialize the keyboard listener for recording controls and rerun visualization
_, events = init_keyboard_listener()  # events dict contains flags like 'stop_recording', 'rerecord_episode'
init_rerun(session_name="recording")  # Start Rerun for real-time data visualization

# Connect the robot and teleoperator to hardware
robot.connect()
teleop.connect()

# Main recording loop - iterate through episodes
episode_idx = 0
while episode_idx < NUM_EPISODES and not events["stop_recording"]:
    log_say(f"Recording episode {episode_idx + 1} of {NUM_EPISODES}")

    # Record a single episode with teleoperation
    record_loop(
        robot=robot,                          # Multi-arm follower robot to record
        events=events,                        # Keyboard event flags
        fps=FPS,                              # Recording frame rate
        teleop=teleop,                        # Multi-arm leader for control
        dataset=dataset,                      # Dataset to store recordings
        control_time_s=EPISODE_TIME_SEC,      # Maximum episode duration
        single_task=TASK_DESCRIPTION,         # Task description for metadata
        display_data=True,                    # Enable real-time visualization
    )

    # Reset the environment if not stopping or re-recording
    # Skip reset after the last episode unless re-recording
    if not events["stop_recording"] and (episode_idx < NUM_EPISODES - 1 or events["rerecord_episode"]):
        log_say("Reset the environment")
        # Record reset movements without saving to dataset
        record_loop(
            robot=robot,
            events=events,
            fps=FPS,
            teleop=teleop,
            control_time_s=RESET_TIME_SEC,
            single_task=TASK_DESCRIPTION,
            display_data=True,
        )

    # Handle re-recording request
    if events["rerecord_episode"]:
        log_say("Re-recording episode")
        # Reset flags and clear buffered data
        events["rerecord_episode"] = False
        events["exit_early"] = False
        dataset.clear_episode_buffer()
        continue  # Restart the loop without incrementing episode_idx

    # Save the completed episode to dataset
    dataset.save_episode()
    episode_idx += 1

# Clean up resources
log_say("Stop recording")
robot.disconnect()      # Disconnect follower robots
teleop.disconnect()     # Disconnect leader arms
dataset.push_to_hub()   # Upload the complete dataset to HuggingFace Hub
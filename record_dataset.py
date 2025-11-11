"""
Dataset recording script for SO100 robotic arm teleoperation.

This script records demonstration episodes of a robot performing tasks under human
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
from lerobot.robots.so100_follower import SO101Follower, SO101FollowerConfig
from lerobot.teleoperators.so100_leader.config_so100_leader import SO101LeaderConfig
from lerobot.teleoperators.so100_leader.so100_leader import SO101Leader
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
# Configure camera(s) - "front" camera using OpenCV at 640x480 resolution
camera_config = {"front": OpenCVCameraConfig(index_or_path=0, width=640, height=480, fps=FPS)}

# Configure the follower robot (the arm that performs the task)
robot_config = SO101FollowerConfig(
    port="/dev/tty.usbmodem58760434471",     # Serial port for follower arm
    id="my_awesome_follower_arm",             # Unique identifier for the robot
    cameras=camera_config                      # Attach camera configuration
)

# Configure the leader arm (used for teleoperation control)
teleop_config = SO101LeaderConfig(
    port="/dev/tty.usbmodem585A0077581",      # Serial port for leader arm
    id="my_awesome_leader_arm"                 # Unique identifier for teleop device
)

# Initialize the robot and teleoperator instances
robot = SO101Follower(robot_config)
teleop = SO101Leader(teleop_config)

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
        robot=robot,                          # Follower robot to record
        events=events,                        # Keyboard event flags
        fps=FPS,                              # Recording frame rate
        teleop=teleop,                        # Leader arm for control
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
robot.disconnect()      # Disconnect follower robot
teleop.disconnect()     # Disconnect leader arm
dataset.push_to_hub()   # Upload the complete dataset to HuggingFace Hub
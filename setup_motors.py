"""
Motor setup script for SO101 robotic arms.

This script provides a command-line interface to configure and initialize motors
for SO101 leader and follower arms. Motor setup includes configuring motor parameters,
communication settings, and operational modes.

Usage:
    python setup_motors.py --port USB0 --id my_robot --arm_type leader
    python setup_motors.py -p USB0 -i my_robot -a follower
"""
from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig
from lerobot.teleoperators.so101_leader import SO101Leader, SO101LeaderConfig
import argparse


def get_arm(arm_type, port, id):
    """
    Factory function to create and configure an arm instance.
    
    Args:
        arm_type (str): Type of arm - either "follower" or "leader"
        port (str): Serial port path (e.g., "/dev/ttyUSB0")
        id (str): Unique identifier for the robot
    
    Returns:
        SO101Follower or SO101Leader: Configured arm instance
    
    Raises:
        ValueError: If arm_type is not "leader" or "follower"
    """
    if arm_type == "follower":
        # Configure and create follower arm
        config = SO101FollowerConfig(
            port=port,
            id=id,
        )
        arm = SO101Follower(config)
    elif arm_type == "leader":
        # Configure and create leader arm
        config = SO101LeaderConfig(
            port=port,
            id=id,
        )
        arm = SO101Leader(config)
    else:
        raise ValueError("Invalid arm_type. Must be 'leader' or 'follower'.")
    
    return arm

def setup_motors(port, id, arm_type):
    """
    Initialize and configure motors for the specified SO101 arm.
    
    This function sets up motor communication, parameters, and operational modes
    required for the arm to function properly.
    
    Args:
        port (str): Serial port path (e.g., "/dev/ttyUSB0")
        id (str): Unique identifier for the robot
        arm_type (str): Type of arm - either "follower" or "leader"
    """
    # Initialize arm instance
    arm = get_arm(arm_type, port, id)
    
    # Configure and initialize motors
    arm.setup_motors()


if __name__ == "__main__":
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description="Setup SO101 motors")
    parser.add_argument("--port", "-p", required=True, help="Serial port (e.g. if /dev/ttyUSB0 pass USB0)")
    parser.add_argument("--id", "-i", required=True, help="Unique robot identifier")
    parser.add_argument("--arm_type", "-a", choices=("leader", "follower"), required=True, help="Arm type: leader or follower")
    args = parser.parse_args()

    # Execute motor setup with formatted port path
    setup_motors(f"/dev/tty{args.port}", args.id, args.arm_type)
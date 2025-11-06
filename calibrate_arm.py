"""
Calibration script for SO101 robotic arms.

This script provides a command-line interface to calibrate SO101 leader and follower arms.
Calibration is required to establish proper zero positions and operational ranges for the arm servos.

Usage:
    python calibrate_arm.py --port USB0 --id my_robot --arm_type leader
    python calibrate_arm.py -p USB0 -i my_robot -a follower
"""
import argparse
from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig
from lerobot.teleoperators.so101_leader import SO101Leader, SO101LeaderConfig

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

def calibrate_arm(port, id, arm_type):
    """
    Calibrate the specified SO101 arm.
    
    This function connects to the arm, performs calibration to establish servo
    zero positions and ranges, then disconnects.
    
    Args:
        port (str): Serial port path (e.g., "/dev/ttyUSB0")
        id (str): Unique identifier for the robot
        arm_type (str): Type of arm - either "follower" or "leader"
    """
    # Initialize arm instance
    arm = get_arm(arm_type, port, id)
    
    # Connect to the arm without auto-calibration
    arm.connect(calibrate=False)
    
    # Perform manual calibration
    arm.calibrate()
    
    # Clean up connection
    arm.disconnect()

if __name__ == "__main__":
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description="Calibrate SO101 arm")
    parser.add_argument("--port", "-p", required=True, help="Serial port (e.g. if /dev/ttyUSB0 pass USB0)")
    parser.add_argument("--id", "-i", required=True, help="Unique robot identifier")
    parser.add_argument("--arm_type", "-a", choices=("leader", "follower"), required=True, help="Arm type: leader or follower")
    args = parser.parse_args()

    # Execute calibration with formatted port path
    calibrate_arm(f"/dev/tty{args.port}", args.id, args.arm_type)
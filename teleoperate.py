"""
Teleoperation script for SO101 robotic arm pairs.

This script enables real-time teleoperation where leader arms control follower arms.
It supports up to 2 simultaneous robot pairs, each running in a separate thread for
parallel operation. The script captures the initial position and returns robots to
that position on exit.

Usage:
    # Single pair
    python teleoperate.py --follower_port1 USB0 --follower_id1 follower1 --leader_port1 USB1 --leader_id1 leader1
    
    # Two pairs
    python teleoperate.py -fp1 USB0 -fi1 follower1 -lp1 USB1 -li1 leader1 -fp2 USB2 -fi2 follower2 -lp2 USB3 -li2 leader2
"""
import argparse
import threading
from lerobot.teleoperators.so101_leader import SO101LeaderConfig, SO101Leader
from lerobot.robots.so101_follower import SO101FollowerConfig, SO101Follower
import pathlib

def operate_robot_pair(robot, teleop_device, pair_name, stop_event):
    """
    Run teleoperation loop for a single robot pair.
    
    This function continuously reads actions from the leader arm and sends them
    to the follower robot. On interruption, it returns the robot to its initial
    position and disconnects both devices.
    
    Args:
        robot (SO101Follower): The follower robot that will execute actions
        teleop_device (SO101Leader): The leader arm that provides control input
        pair_name (str): Identifier for this robot pair (e.g., "Pair 1")
        stop_event (threading.Event): Event to signal thread shutdown
    """
    # Capture initial position to return to on exit
    initial_position = robot.get_observation()
    
    try:
        # Main teleoperation loop: continuously mirror leader movements to follower
        while not stop_event.is_set():
            # Read current position/action from leader arm
            action = teleop_device.get_action()
            # Send action to follower robot
            robot.send_action(action)
    except Exception as e:
        print(f"\n{pair_name} encountered error: {e}")
    finally:
        # Cleanup: return to initial position and disconnect
        print(f"Moving {pair_name} robot back to initial position...")
        robot.send_action(initial_position)
        robot.disconnect()
        teleop_device.disconnect()

if __name__ == "__main__":
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description="Teleoperate SO101 follower arms with leader arms (supports up to 2 pairs)")
    
    # Pair 1 arguments (required)
    parser.add_argument("--follower_port1", "-fp1", required=True, help="Serial port for follower robot 1 (e.g. USB0)")
    parser.add_argument("--follower_id1", "-fi1", required=True, help="Unique identifier for follower robot 1")
    parser.add_argument("--leader_port1", "-lp1", required=True, help="Serial port for leader arm 1 (e.g. USB1)")
    parser.add_argument("--leader_id1", "-li1", required=True, help="Unique identifier for leader arm 1")

    # Pair 2 arguments (optional - for dual arm operation)
    parser.add_argument("--follower_port2", "-fp2", required=False, help="Serial port for follower robot 2 (e.g. USB2)")
    parser.add_argument("--follower_id2", "-fi2", required=False, help="Unique identifier for follower robot 2")
    parser.add_argument("--leader_port2", "-lp2", required=False, help="Serial port for leader arm 2 (e.g. USB3)")
    parser.add_argument("--leader_id2", "-li2", required=False, help="Unique identifier for leader arm 2")

    # Calibration directory
    parser.add_argument("--calibration_dir", "-cd", required=False, default="calibration", help="Path to calibration directory")
    
    args = parser.parse_args()

    calib_dir = pathlib.Path(args.calibration_dir)

    # Create stop event for coordinating thread shutdown
    stop_event = threading.Event()

    # Setup Pair 1 (required)
    # Configure follower robot 1
    robot_config1 = SO101FollowerConfig(
        port=f"/dev/tty{args.follower_port1}",
        id=args.follower_id1,
        calibration_dir=calib_dir,
    )
    # Configure leader arm 1
    teleop_config1 = SO101LeaderConfig(
        port=f"/dev/tty{args.leader_port1}",
        id=args.leader_id1,
        calibration_dir=calib_dir,
    )
    # Initialize and connect pair 1
    robot1 = SO101Follower(robot_config1)
    teleop_device1 = SO101Leader(teleop_config1)
    robot1.connect()
    teleop_device1.connect()

    # Create thread list with pair 1
    threads = [threading.Thread(target=operate_robot_pair, args=(robot1, teleop_device1, "Pair 1", stop_event), daemon=False)]

    # Setup Pair 2 if all required arguments are provided
    if args.follower_port2 and args.follower_id2 and args.leader_port2 and args.leader_id2:
        # Configure follower robot 2
        robot_config2 = SO101FollowerConfig(
            port=f"/dev/tty{args.follower_port2}",
            id=args.follower_id2,
            calibration_dir=calib_dir,
        )
        # Configure leader arm 2
        teleop_config2 = SO101LeaderConfig(
            port=f"/dev/tty{args.leader_port2}",
            id=args.leader_id2,
            calibration_dir=calib_dir,
        )
        # Initialize and connect pair 2
        robot2 = SO101Follower(robot_config2)
        teleop_device2 = SO101Leader(teleop_config2)
        robot2.connect()
        teleop_device2.connect()
        
        # Add pair 2 thread to list
        threads.append(threading.Thread(target=operate_robot_pair, args=(robot2, teleop_device2, "Pair 2", stop_event), daemon=False))

    print("Starting teleop")
    # Start all teleoperation threads for parallel operation
    for thread in threads:
        thread.start()
    
    try:
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\nShutting down all teleoperation sessions...")
        stop_event.set()  # Signal all threads to stop
        # Wait for threads to finish cleanup
        for thread in threads:
            thread.join(timeout=5.0)
        print("All sessions stopped")
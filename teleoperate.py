import argparse
import threading
from lerobot.teleoperators.so101_leader import SO101LeaderConfig, SO101Leader
from lerobot.robots.so101_follower import SO101FollowerConfig, SO101Follower

def operate_robot_pair(robot, teleop_device, pair_name):
    """Run teleoperation loop for a single robot pair"""
    initial_position = robot.get_observation()
    
    try:
        while True:
            action = teleop_device.get_action()
            robot.send_action(action)
    except KeyboardInterrupt:
        print(f"\n{pair_name} teleoperation interrupted by user")
    finally:
        print(f"Moving {pair_name} robot back to initial position...")
        robot.send_action(initial_position)
        robot.disconnect()
        teleop_device.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Teleoperate SO101 follower arms with leader arms (supports up to 2 pairs)")
    
    # Pair 1 arguments
    parser.add_argument("--follower_port1", "-fp1", required=True, help="Serial port for follower robot 1 (e.g. USB0)")
    parser.add_argument("--follower_id1", "-fi1", required=True, help="Unique identifier for follower robot 1")
    parser.add_argument("--leader_port1", "-lp1", required=True, help="Serial port for leader arm 1 (e.g. USB1)")
    parser.add_argument("--leader_id1", "-li1", required=True, help="Unique identifier for leader arm 1")

    # Pair 2 arguments (optional)
    parser.add_argument("--follower_port2", "-fp2", required=False, help="Serial port for follower robot 2 (e.g. USB2)")
    parser.add_argument("--follower_id2", "-fi2", required=False, help="Unique identifier for follower robot 2")
    parser.add_argument("--leader_port2", "-lp2", required=False, help="Serial port for leader arm 2 (e.g. USB3)")
    parser.add_argument("--leader_id2", "-li2", required=False, help="Unique identifier for leader arm 2")
    
    args = parser.parse_args()

    # Setup Pair 1
    robot_config1 = SO101FollowerConfig(
        port=f"/dev/tty{args.follower_port1}",
        id=args.follower_id1,
    )
    teleop_config1 = SO101LeaderConfig(
        port=f"/dev/tty{args.leader_port1}",
        id=args.leader_id1,
    )
    robot1 = SO101Follower(robot_config1)
    teleop_device1 = SO101Leader(teleop_config1)
    robot1.connect()
    teleop_device1.connect()

    threads = [threading.Thread(target=operate_robot_pair, args=(robot1, teleop_device1, "Pair 1"), daemon=False)]

    # Setup Pair 2 if provided
    if args.follower_port2 and args.follower_id2 and args.leader_port2 and args.leader_id2:
        robot_config2 = SO101FollowerConfig(
            port=f"/dev/tty{args.follower_port2}",
            id=args.follower_id2,
        )
        teleop_config2 = SO101LeaderConfig(
            port=f"/dev/tty{args.leader_port2}",
            id=args.leader_id2,
        )
        robot2 = SO101Follower(robot_config2)
        teleop_device2 = SO101Leader(teleop_config2)
        robot2.connect()
        teleop_device2.connect()
        
        threads.append(threading.Thread(target=operate_robot_pair, args=(robot2, teleop_device2, "Pair 2"), daemon=False))

    # Start all threads and wait for completion
    for thread in threads:
        thread.start()
    
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\nAll teleoperation sessions interrupted by user")
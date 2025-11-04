import argparse
from lerobot.teleoperators.so101_leader import SO101LeaderConfig, SO101Leader
from lerobot.robots.so101_follower import SO101FollowerConfig, SO101Follower

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Teleoperate SO101 follower arm with leader arm")
    parser.add_argument("--robot_port", "-rp", required=True, help="Serial port for follower robot (e.g. USB0)")
    parser.add_argument("--robot_id", "-ri", required=True, help="Unique identifier for follower robot")
    parser.add_argument("--leader_port", "-lp", required=True, help="Serial port for leader arm (e.g. USB1)")
    parser.add_argument("--leader_id", "-li", required=True, help="Unique identifier for leader arm")
    args = parser.parse_args()

    robot_config = SO101FollowerConfig(
        port=f"/dev/tty{args.robot_port}",
        id=args.robot_id,
    )

    teleop_config = SO101LeaderConfig(
        port=f"/dev/tty{args.leader_port}",
        id=args.leader_id,
    )

    robot = SO101Follower(robot_config)
    teleop_device = SO101Leader(teleop_config)
    robot.connect()
    teleop_device.connect()

    initial_position = robot.get_observation()

    try:
        while True:
            action = teleop_device.get_action()
            robot.send_action(action)
    except KeyboardInterrupt:
        print("\nTeleoperation interrupted by user")
    finally:
        print("Moving robot back to initial position...")
        robot.send_action(initial_position)
        robot.disconnect()
        teleop_device.disconnect()
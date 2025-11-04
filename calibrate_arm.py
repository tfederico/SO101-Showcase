import argparse
from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig
from lerobot.teleoperators.so101_leader import SO101Leader, SO101LeaderConfig

def get_arm(arm_type, port, id):
    if arm_type == "follower":
        config = SO101FollowerConfig(
            port=port,
            id=id,
        )
        arm = SO101Follower(config)
    elif arm_type == "leader":
        config = SO101LeaderConfig(
            port=port,
            id=id,
        )
        arm = SO101Leader(config)
    else:
        raise ValueError("Invalid arm_type. Must be 'leader' or 'follower'.")
    return arm

def calibrate_arm(port, id, arm_type):
    arm = get_arm(arm_type, port, id)
    arm.connect(calibrate=False)
    arm.calibrate()
    arm.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calibrate SO101 arm")
    parser.add_argument("--port", "-p", required=True, help="Serial port (e.g. if /dev/ttyUSB0 pass USB0)")
    parser.add_argument("--id", "-i", required=True, help="Unique robot identifier")
    parser.add_argument("--arm_type", "-a", choices=("leader", "follower"), required=True, help="Arm type: leader or follower")
    args = parser.parse_args()

    calibrate_arm(f"/dev/tty{args.port}", args.id, args.arm_type)
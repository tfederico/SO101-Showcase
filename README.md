# SO101 Showcase

This repository contains scripts for controlling and calibrating SO101 robotic arms, including teleoperation capabilities.

## Repository Structure

```
SO101-Showcase/
├── find_port.sh          # Find the ports to which the robots are connected
├── enable_port.sh        # Enable the ports to which the robots are connected
├── calibrate_arm.py      # Calibrate SO101 arms (leader or follower)
├── teleoperate.py        # Teleoperate follower arm using leader arm
├── setup_motors.py       # Setup the motors of the arms
└── README.md             # This file
```

## Scripts

### `setup_motors.py`

Assign IDs to the motors of the SO101 arm (either leader or follower type)
.
**Usage:**
```bash
python setup_motors.py --port PORT --id NAME --arm_type TYPE
```

**Arguments:**
- `--port, -p` (required): Serial port identifier (e.g., `USB0` for `/dev/ttyUSB0`)
- `--id, -i` (required): Unique identifier for the robot arm
- `--arm_type, -a` (required): Arm type - `leader` or `follower`

### `calibrate_arm.py`

Calibrates a SO101 arm (either leader or follower type) by performing initial calibration routines.

**Usage:**
```bash
python calibrate_arm.py --port PORT --id NAME --arm_type TYPE
```

**Arguments:**
- `--port, -p` (required): Serial port identifier (e.g., `USB0` for `/dev/ttyUSB0`)
- `--id, -i` (required): Unique identifier for the robot arm
- `--arm_type, -a` (required): Arm type - `leader` or `follower`

### teleoperate.py

Enables real-time teleoperation of a follower SO101 arm controlled by a leader SO101 arm.

**Usage:**
```bash
python teleoperate.py --robot_port PORT1 --robot_id NAME1 --leader_port PORT2 --leader_id NAME2
```

**Arguments:**
- `--robot_port, -rp` (required): Serial port for follower robot (e.g., `USB0`)
- `--robot_id, -ri` (required): Unique identifier for follower robot
- `--leader_port, -lp` (required): Serial port for leader arm (e.g., `USB1`)
- `--leader_id, -li` (required): Unique identifier for leader arm

**Features:**
- Real-time action streaming from leader to follower
- Graceful interruption with `Ctrl+C`
- Automatic return to initial position on exit

## Requirements

- Python 3.10+
- LeRobot library with SO101 support
- Appropriate USB/serial drivers for arm communication
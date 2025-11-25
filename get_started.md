# Instructions

## Connecting devices

- Connect 5V power supplies to the leader arms. Connect the 12V power supplies to the follower arms.
- Connect all USB-C cables to the arms and connect the USB-C hub to the pc.
- Insert the USB-C cables in the USB-C hub in the specific order (e.g., A, B, C, D). This ensures the correct mapping between the robotic arms and the ports.
- Connect all JST to USB-A cables from the cameras to the USB-A hub that is connected to the pc in the specific order (e.g., 1, 2, 3). This is to ensure the IDs of the cameras are correct.
- Connect the IntelRealsense camera to the USB-A hub.

## Enable ports

If the robots were connected in the correct order, you can enable the communication through the ports using

```
sudo chmod 666 /dev/ttyACM0
sudo chmod 666 /dev/ttyACM1
sudo chmod 666 /dev/ttyACM2
sudo chmod 666 /dev/ttyACM3
```

You can always use `lerobot-find-port` to identify the ports assigned to each robot.

## Find cameras

These steps are only necessary if you did not connect the cameras in the right order or if they were detected in a different order.

Run `conda activate lerobot` to activate the environment.

Run `lerobot-find-cameras realsense` to get the serial number of the camera.

Run `lerobot-find-cameras opencv` to find all the other cameras. This will find any camera (including webcams) connected to the pc.
To find the IDs of your cameras, check the `outputs/captured_images` folder to match the photo taken by the camera to the ID.

### Edit configs

Edit the `configs.json` file with the IDs of the cameras.

## Record an episode

Run `python record_single_episode.py`
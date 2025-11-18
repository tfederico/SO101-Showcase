"""
RealSense camera test script.

This script demonstrates basic usage of the Intel RealSense camera with the LeRobot
framework. It configures the camera, captures both RGB color frames and depth maps,
and displays their dimensions to verify proper functionality.

Usage:
    python test_realsense_camera.py

Note:
    Update the serial_number_or_name with your camera's actual serial number.
"""
from lerobot.cameras.realsense.configuration_realsense import RealSenseCameraConfig
from lerobot.cameras.realsense.camera_realsense import RealSenseCamera
from lerobot.cameras.configs import ColorMode, Cv2Rotation
import matplotlib.pyplot as plt

# Configure the RealSense camera with desired parameters
config = RealSenseCameraConfig(
    serial_number_or_name="243322073128",  # Unique serial number of the RealSense camera
    fps=15,                                 # Frame rate: 15 frames per second
    width=640,                              # Image width in pixels
    height=480,                             # Image height in pixels
    color_mode=ColorMode.RGB,               # Color format: RGB (Red-Green-Blue)
    use_depth=True,                         # Enable depth sensing capability
    rotation=Cv2Rotation.NO_ROTATION        # No image rotation applied
)

# Initialize the camera with the configuration and connect to the device
# The connection includes a warm-up period to stabilize the camera feed
camera = RealSenseCamera(config)
camera.connect()

# Capture and display frame information
try:
    # Capture a single RGB color frame
    color_frame = camera.read()
    
    # Capture a single depth map (distance information for each pixel)
    depth_map = camera.read_depth()
    
    # Display the dimensions of captured frames for verification
    print("Color frame shape:", color_frame.shape)  # Expected: (480, 640, 3) for RGB
    print("Depth map shape:", depth_map.shape)      # Expected: (480, 640) for depth
    
    # Visualize the RGB image
    plt.figure(figsize=(10, 8))
    plt.imshow(color_frame)
    plt.title("RealSense RGB Image")
    plt.axis('off')
    plt.show()
finally:
    # Always disconnect the camera to release hardware resources
    camera.disconnect()
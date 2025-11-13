"""
Wrist camera test script using OpenCV.

This script demonstrates basic usage of an OpenCV-based camera (typically a USB webcam
or wrist-mounted camera) with the LeRobot framework. It configures the camera for
high-resolution capture and tests asynchronous frame reading with timeout handling.

Usage:
    python test_wrist_camera.py

Note:
    Update the index_or_path if your camera is not at device index 0.
"""
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.cameras.opencv.camera_opencv import OpenCVCamera
from lerobot.cameras.configs import ColorMode, Cv2Rotation
import cv2

# Configure the OpenCV camera with desired parameters
config = OpenCVCameraConfig(
    index_or_path=4,                        # Camera device index (0 for default camera, or use path like "/dev/video0")
    fps=30,                                 # Frame rate: 30 frames per second
    width=640,                             # Image width in pixels (HD)
    height=480,                            # Image height in pixels (HD)
    color_mode=ColorMode.RGB,               # Color format: RGB (Red-Green-Blue)
    rotation=Cv2Rotation.NO_ROTATION        # No image rotation applied
)

# Initialize the camera with the configuration and connect to the device
# The connection includes a warm-up period to stabilize the camera feed
camera = OpenCVCamera(config)
camera.connect()

# Capture frames asynchronously to test non-blocking frame acquisition
try:
    # Read 10 frames asynchronously to verify camera functionality
    frames = []
    for i in range(10):
        # Asynchronously read a frame with 200ms timeout
        # This allows the main thread to continue if frame capture takes too long
        frame = camera.async_read(timeout_ms=200)
        frames.append(frame)
        
        # Display frame dimensions for verification
        print(f"Async frame {i} shape:", frame.shape)  # Expected: (480, 640, 3) for RGB
    
    # Display the captured frames
    print("\nDisplaying frames. Press any key to advance, 'q' to quit.")
    for i, frame in enumerate(frames):
        # Convert RGB to BGR for OpenCV display
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow(f'Frame {i}', frame_bgr)
        key = cv2.waitKey(0)
        if key == ord('q'):
            break
        cv2.destroyAllWindows()
    
    cv2.destroyAllWindows()
finally:
    # Always disconnect the camera to release hardware resources
    camera.disconnect()
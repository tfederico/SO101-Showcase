# Installation instructions

## Installing LeRobot

Create conda environment
`conda create -y -n lerobot python=3.10`

Activate environment
`conda activate lerobot`

Install ffmpeg
`conda install ffmpeg -c conda-forge`

Install LeRobot
`pip install 'lerobot[all]`

If you encounter build errors, you may need to install additional dependencies: cmake, build-essential, and ffmpeg libs. To install these for linux run:
`sudo apt-get install cmake build-essential python-dev pkg-config libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libswresample-dev libavfilter-dev pkg-config`

## Installing Realsense SDK 2.0

Register the server's public key:

```
sudo mkdir -p /etc/apt/keyrings
curl -sSf https://librealsense.intel.com/Debian/librealsense.pgp | sudo tee /etc/apt/keyrings/librealsense.pgp > /dev/null
```

Make sure apt HTTPS support is installed: 
`sudo apt-get install apt-transport-https`

Add the server to the list of repositories:
```
echo "deb [signed-by=/etc/apt/keyrings/librealsense.pgp] https://librealsense.intel.com/Debian/apt-repo `lsb_release -cs` main" | \
sudo tee /etc/apt/sources.list.d/librealsense.list
sudo apt-get update
```

Install the libraries
```
sudo apt-get install librealsense2-dkms
sudo apt-get install librealsense2-utils
```

Optionally install the developer and debug packages:
```
sudo apt-get install librealsense2-dev
sudo apt-get install librealsense2-dbg
```

To test, Reconnect the Intel RealSense depth camera and run: `realsense-viewer` to verify the installation.
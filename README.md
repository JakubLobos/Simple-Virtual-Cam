# VirtualCam

Stream any video file as a virtual webcam. Works in browsers, Zoom, Teams, Discord — anywhere you can select a camera.

## Requirements

| Platform | Driver needed |
|----------|--------------|
| Windows  | [OBS Studio](https://obsproject.com) (just install it, no need to open it) |
| macOS    | [OBS Studio](https://obsproject.com) — open it once and click **Start Virtual Camera** to register the driver |
| Linux    | `v4l2loopback` (installed automatically by `install.sh`) |

Python 3.8+ is required on all platforms.

## Installation

**Windows**
```bat
install.bat
```

**macOS / Linux**
```bash
chmod +x install.sh
./install.sh
```

Or manually:
```bash
pip3 install -r requirements.txt
```

## Usage

**Windows**
```bat
py app.py
```

**macOS / Linux**
```bash
python3 app.py
```

1. Click **Choose file** and select a video (MP4, AVI, MOV, MKV, WEBM)
2. Click **Start streaming**
3. In your browser or app, select **OBS Virtual Camera** as your camera source
4. Click **Stop streaming** when done

## Why this exists

Some applications (proctoring software, anti-cheat systems, etc.) detect and block the `obs.exe` process, making it impossible to use OBS Studio directly. VirtualCam works around this — it only uses the virtual camera driver that OBS installs, without ever launching OBS itself. The `obs.exe` process never runs, so it stays undetected.

## How it works

VirtualCam uses [pyvirtualcam](https://github.com/letmaik/pyvirtualcam) to push video frames directly into the OBS virtual camera driver (Windows/macOS) or v4l2loopback (Linux). OBS Studio only needs to be installed for its driver — it does not need to be running.

The video loops automatically when it reaches the end.

## License

MIT

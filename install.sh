#!/bin/bash
set -e

pip install -r requirements.txt

OS="$(uname -s)"

if [ "$OS" = "Linux" ]; then
    echo ""
    echo "Installing v4l2loopback..."
    sudo apt-get install -y v4l2loopback-dkms 2>/dev/null || \
    sudo dnf install -y v4l2loopback 2>/dev/null || \
    echo "Install v4l2loopback manually for your distro."
    sudo modprobe v4l2loopback
    echo "v4l2loopback loaded."
elif [ "$OS" = "Darwin" ]; then
    echo ""
    echo "macOS: install OBS Studio from obsproject.com"
    echo "Then open OBS once and start Virtual Camera to register the driver."
fi

echo ""
echo "Done! Run the app with: python3 app.py"

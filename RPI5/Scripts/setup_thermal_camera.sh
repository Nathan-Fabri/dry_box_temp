#!/bin/bash
# DryBox Thermal Camera Setup Script
# This script installs the thermal camera dependencies

echo "🌡️ DryBox Thermal Camera Setup"
echo "================================"

# Check if we're on Raspberry Pi
if [ -f /etc/rpi-issue ] || [ -f /proc/device-tree/model ]; then
    echo "📟 Detected Raspberry Pi - applying optimizations..."
    RPI_DETECTED=true
else
    echo "💻 Running on generic Linux system"
    RPI_DETECTED=false
fi

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install system dependencies for OpenCV
echo "📦 Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgtk-3-0 \
    v4l-utils \
    libv4l-dev

# Install OpenCV
echo "📦 Installing OpenCV for Python..."
pip3 install opencv-python

# Test OpenCV installation
echo "🧪 Testing OpenCV installation..."
python3 -c "import cv2; print(f'✅ OpenCV version: {cv2.__version__}')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ OpenCV installed successfully!"
else
    echo "❌ OpenCV installation failed. Trying alternative..."
    pip3 install opencv-python-headless
    
    python3 -c "import cv2; print(f'✅ OpenCV version: {cv2.__version__}')" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ OpenCV (headless) installed successfully!"
    else
        echo "❌ Failed to install OpenCV. Please install manually with:"
        echo "   pip3 install opencv-python"
        exit 1
    fi
fi

# Set up camera permissions
echo "🔧 Setting up camera permissions..."
sudo usermod -a -G video $USER

# Configure GPU memory on Raspberry Pi
if [ "$RPI_DETECTED" = true ]; then
    echo "🎮 Checking GPU memory configuration..."
    
    if command -v vcgencmd &> /dev/null; then
        current_gpu_mem=$(vcgencmd get_mem gpu | cut -d'=' -f2 | cut -d'M' -f1)
        if [ "$current_gpu_mem" -lt 128 ]; then
            echo "⚠️  GPU memory is set to ${current_gpu_mem}M. Recommended: 128M"
            echo "   To increase GPU memory, run: sudo raspi-config"
            echo "   Go to: Advanced Options > Memory Split > Set to 128"
        else
            echo "✅ GPU memory is optimally configured (${current_gpu_mem}M)"
        fi
    fi
fi

# Test camera detection
echo "🔍 Testing camera detection..."
for i in {0..3}; do
    if python3 -c "import cv2; cap = cv2.VideoCapture($i); success = cap.isOpened(); cap.release(); exit(0 if success else 1)" 2>/dev/null; then
        echo "   ✅ Camera detected at index $i"
        break
    fi
done

echo ""
echo "🎉 Setup complete! Thermal camera support is now available."
echo ""
echo "📋 Next steps:"
echo "   1. Restart your DryBox web server"
echo "   2. Navigate to http://your-pi-ip:5000/thermal"
echo "   3. Click 'Start Camera' to begin thermal imaging"
echo ""
echo "💡 Tips:"
echo "   - Make sure your TOPDON TC001 is connected via USB"
echo "   - You may need to logout and login for camera permissions"
echo "   - Check /dev/video* devices if camera isn't detected"

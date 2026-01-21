#!/usr/bin/env python3
"""shutdown 
DryBox Web Control Interface

A Flask web server that provides a web interface to start and stop the DryBox system.
It includes buttons to control the system and displays the relevant log files.
"""

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import subprocess
import os
import time
import threading
import datetime
import json
import shutil
import jsonschema
import glob

# Try to import OpenCV for thermal camera support
try:
    import cv2
    import numpy as np
    THERMAL_CAMERA_AVAILABLE = True
    print("✅ Thermal camera support available (OpenCV found)")
except ImportError:
    THERMAL_CAMERA_AVAILABLE = False
    print("⚠️  Thermal camera support disabled (OpenCV not found)")
    print("   Install OpenCV with: pip install opencv-python")

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

# Define paths dynamically based on script location
# Get the directory where this script is located (Python folder)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to get RPI5 directory
BASE_DIR = os.path.dirname(SCRIPT_DIR)
LOG_DIR = os.path.join(BASE_DIR, "DataLogging")
JSON_DIR = os.path.join(BASE_DIR, "JSONS")
SCRIPTS_DIR = os.path.join(BASE_DIR, "Scripts")

# Define paths for scripts
START_SCRIPT = os.path.join(SCRIPTS_DIR, "start_drybox.sh")
STOP_SCRIPT = os.path.join(SCRIPTS_DIR, "stop_drybox.sh")
FLASH_SCRIPT = os.path.join(SCRIPTS_DIR, "flash_teensy.sh")

# Define paths for log files
STARTUP_LOG = os.path.join(LOG_DIR, "drybox_startup.log")
SHUTDOWN_LOG = os.path.join(LOG_DIR, "drybox_shutdown.log")
JSONPARSE_LOG = os.path.join(LOG_DIR, "jsonParse.log")
SERIALDEBUG_LOG = os.path.join(LOG_DIR, "serialDebug.log")
FLASH_LOG = os.path.join(LOG_DIR, "teensy_flash.log")
CURRENT_LAYER_INFO = os.path.join(LOG_DIR, "current_layer.txt")
NEXT_LAYER_TRIGGER = os.path.join(LOG_DIR, "next_layer.trigger")
PREV_LAYER_TRIGGER = os.path.join(LOG_DIR, "prev_layer.trigger")
JUMP_TO_LAYER_TRIGGER = os.path.join(LOG_DIR, "jump_to_layer.trigger")
NEXT_STEP_TRIGGER = os.path.join(LOG_DIR, "next_step.trigger")
PREV_STEP_TRIGGER = os.path.join(LOG_DIR, "prev_step.trigger")

# Define path for shellJson.json
SHELL_JSON = os.path.join(JSON_DIR, "shellJson.json")
SCHEMA_FILE = os.path.join(JSON_DIR, "schema")
IDLE_CONFIG_PATH = os.path.join(JSON_DIR, "idleConfig.json")

# Global variables to track system state
system_running = False
last_action = None
last_action_time = None

# Thermal camera global instance
thermal_camera = None

class ThermalCamera:
    """Enhanced thermal camera class for DryBox integration with TOPDON TC001 support"""
    
    def __init__(self, camera_index=0):
        # Initialize essential attributes first (before any early returns)
        self.available = False
        self.serial_connections = {}
        self.last_reconnect_attempt = {}
        self.reconnect_interval = 10.0
        self.last_connection_check = 0
        self.connection_check_interval = 30.0
        self.test_mode_enabled = False
        self.test_temperature = 42.5
        self.last_test_send = 0
        self.last_measurement_send = 0
        self.custom_measurement_points = []
        
        if not THERMAL_CAMERA_AVAILABLE:
            return
            
        self.camera_index = camera_index
        self.cap = None
        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        
        # TOPDON TC001 specific settings
        self.width = 256
        self.height = 192
        self.colormap = cv2.COLORMAP_INFERNO
        self.fps = 25
        
        # Temperature tracking
        self.current_min_temp = 0.0
        self.current_max_temp = 100.0
        self.current_avg_temp = 25.0
        self.center_temperature = 25.0
        self.raw_thermal_data = None
        self.temperature_data = None
        self.temp_offset = 0.0
        self.dual_stream_mode = False
        
        # Region of Interest (ROI) for temperature analysis
        self.roi_box = None  # Will store {x1, y1, x2, y2} coordinates
        
        # Serial communication for Teensy
        self.teensy_serial_ports = {
            'left': '/dev/serial/by-id/usb-Teensyduino_Triple_Serial_13142960-if04',
            'right': '/dev/serial/by-id/usb-Teensyduino_Triple_Serial_13142880-if04'
        }
        self._init_teensy_serial()
        
        # Frame counter for debugging
        self._frame_count = 0
        
        # Warning flags to prevent repeated logging
        self._logged_stream_mode_warning = False
        self._logged_unexpected_dimensions = False
        
    def _init_teensy_serial(self):
        """Initialize serial connections to Teensy controllers"""
        print("🔌 Initializing Teensy serial connections...")
        try:
            import serial
            print("✓ pyserial module imported successfully")
            for zone, port in self.teensy_serial_ports.items():
                print(f"🔍 Attempting to connect to Teensy {zone.upper()} on {port}")
                try:
                    ser = serial.Serial(port, 115200, timeout=0.1)
                    self.serial_connections[zone] = ser
                    print(f"✓ Connected to Teensy {zone.upper()} on {port}")
                except Exception as e:
                    print(f"❌ Could not connect to Teensy {zone.upper()}: {e}")
                    print(f"   Port: {port}")
                    print(f"   Error type: {type(e).__name__}")
                    self.serial_connections[zone] = None
        except ImportError:
            print("❌ pyserial not available. Install with: pip install pyserial")
            
        # Show final connection status
        print("🔌 Final serial connection status:")
        for zone, conn in self.serial_connections.items():
            status = "✓ Connected" if conn else "❌ Failed"
            print(f"   {zone.upper()}: {status}")
            # Initialize reconnect tracking
            self.last_reconnect_attempt[zone] = 0
            
    def _attempt_teensy_reconnection(self, zone):
        """Attempt to reconnect to a specific Teensy (non-blocking)"""
        current_time = time.time()
        
        # Only attempt reconnection every reconnect_interval seconds
        if current_time - self.last_reconnect_attempt.get(zone, 0) < self.reconnect_interval:
            return False
            
        self.last_reconnect_attempt[zone] = current_time
        
        print(f"🔄 Attempting to reconnect to Teensy {zone.upper()}...")
        try:
            # Close existing connection if any
            if self.serial_connections.get(zone):
                try:
                    self.serial_connections[zone].close()
                except:
                    pass
                    
            # Attempt new connection
            import serial
            port = self.teensy_serial_ports[zone]
            ser = serial.Serial(port, 115200, timeout=0.1)
            self.serial_connections[zone] = ser
            print(f"✓ Successfully reconnected to Teensy {zone.upper()}")
            return True
            
        except Exception as e:
            print(f"❌ Reconnection failed for Teensy {zone.upper()}: {e}")
            self.serial_connections[zone] = None
            return False
            
    def _check_serial_connections(self):
        """Periodically check and maintain serial connections"""
        current_time = time.time()
        
        # Only check every connection_check_interval seconds
        if current_time - self.last_connection_check < self.connection_check_interval:
            return
            
        self.last_connection_check = current_time
        print("🔍 Checking serial connection health...")
        
        for zone in self.teensy_serial_ports.keys():
            conn = self.serial_connections.get(zone)
            
            if conn is None:
                print(f"⚠️ Teensy {zone.upper()} connection is None, attempting reconnection...")
                self._attempt_teensy_reconnection(zone)
            elif not conn.is_open:
                print(f"⚠️ Teensy {zone.upper()} connection is closed, attempting reconnection...")
                self.serial_connections[zone] = None
                self._attempt_teensy_reconnection(zone)
            else:
                # Connection appears healthy
                print(f"✓ Teensy {zone.upper()} connection is healthy")
            
    def _send_to_teensy(self, temperature, zone):
        """Send temperature to specific Teensy with automatic reconnection"""
        try:
            # Check if connection exists and is valid
            if zone not in self.serial_connections or self.serial_connections[zone] is None:
                print(f"❌ No serial connection for Teensy {zone.upper()}")
                # Attempt reconnection
                if self._attempt_teensy_reconnection(zone):
                    # If reconnection successful, continue with sending
                    pass
                else:
                    return  # Still no connection after reconnect attempt
                
            ser = self.serial_connections[zone]
            
            # Check if connection is still alive
            if not ser.is_open:
                print(f"⚠️ Serial connection to Teensy {zone.upper()} is closed, attempting reconnection...")
                if self._attempt_teensy_reconnection(zone):
                    ser = self.serial_connections[zone]
                else:
                    return
            
            message = f"{temperature:.1f}\n"
            ser.write(message.encode('utf-8'))
            ser.flush()
            print(f"📡 Sent {temperature:.1f}°C to Teensy {zone.upper()}")
            
        except Exception as e:
            print(f"❌ Error sending to Teensy {zone}: {e}")
            # Mark connection as failed and attempt reconnection
            self.serial_connections[zone] = None
            print(f"🔄 Connection lost, will attempt reconnection to Teensy {zone.upper()} in {self.reconnect_interval} seconds")
                
    def send_measurement_to_teensy(self):
        """Send custom measurement point temperature to BOTH Teensys"""
        print("🔍 send_measurement_to_teensy() called")
        
        if not hasattr(self, 'custom_measurement_points') or not self.custom_measurement_points:
            print("❌ No custom measurement points found")
            return  # Send nothing if no measurement points
        
        print(f"📍 Found {len(self.custom_measurement_points)} measurement points")
        
        # Get the first (or most recent) measurement point
        custom_temps = self.get_custom_point_temperatures()
        if not custom_temps:
            print("❌ Could not get temperature data for measurement points")
            return  # Send nothing if can't get temperature
        
        print(f"🌡️ Got temperature data: {custom_temps}")
        
        # Send just the temperature value from the first measurement point
        temp = custom_temps[0]['temperature']
        point = custom_temps[0]
        
        print(f"📡 Sending {temp:.1f}°C from point ({point['x']}, {point['y']}) to BOTH Teensys")
        
        # Send to BOTH Teensys
        self._send_to_teensy(temp, "left")
        self._send_to_teensy(temp, "right")
        
    def enable_test_mode(self, temperature=42.5):
        """Enable test mode with static temperature value"""
        self.test_mode_enabled = True
        self.test_temperature = temperature
        self.last_test_send = 0  # Reset timer
        print(f"🧪 Test mode enabled - sending {temperature}°C every second")
        print(f"🎥 Camera running: {self.running}")
        print(f"� Camera available: {self.available}")
        print(f"�🔌 Serial connections status:")
        for zone, conn in self.serial_connections.items():
            status = "Connected" if conn else "Disconnected"
            print(f"   {zone.upper()}: {status}")
        
        # If camera isn't running, warn the user
        if not self.running:
            print("⚠️  WARNING: Thermal camera is not running! Test mode won't work until camera is started.")
        
    def disable_test_mode(self):
        """Disable test mode"""
        self.test_mode_enabled = False
        print("🧪 Test mode disabled")
        
    def _send_test_data_if_enabled(self):
        """Send test data every second if test mode is enabled"""
        if not self.test_mode_enabled:
            return
            
        current_time = time.time()
        if current_time - self.last_test_send >= 1.0:  # Send every second
            print(f"🧪 TEST MODE: Sending {self.test_temperature}°C")
            self._send_to_teensy(self.test_temperature, "left")
            self.last_test_send = current_time
        
    def cleanup_serial(self):
        """Clean up serial connections"""
        for zone, ser in self.serial_connections.items():
            if ser:
                try:
                    ser.close()
                    print(f"Closed serial connection to Teensy {zone.upper()}")
                except:
                    pass
        
    def initialize_camera(self):
        """Initialize the TOPDON TC001 thermal camera with auto-detection"""
        if not THERMAL_CAMERA_AVAILABLE:
            return False
            
        try:
            # First, try to find the correct camera index
            detected_index = self.find_camera_index()
            if detected_index != self.camera_index:
                print(f"Auto-detected thermal camera at index {detected_index}")
                self.camera_index = detected_index
            
            # Try to open the camera
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                print(f"❌ Could not open camera at index {self.camera_index}")
                return False
            
            # Get actual camera properties first
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            print(f"Camera current settings: {actual_width}x{actual_height}@{actual_fps}fps")
            
            # Set camera properties for TOPDON TC001
            # Important: Don't automatically convert to RGB to preserve thermal data
            self.cap.set(cv2.CAP_PROP_CONVERT_RGB, 0.0)
            
            # First try dual-stream format (256x384 for raw thermal data)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 256)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 384)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Check if dual-stream mode is available
            test_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            test_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if test_height == 384:
                self.dual_stream_mode = True
                print("✅ Dual-stream mode detected (256x384) - real temperature data available")
            else:
                self.dual_stream_mode = False
                # Fallback to standard thermal resolution
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                print("⚠️  Standard mode (256x192) - using temperature approximation")
            
            # TOPDON TC001 specific settings
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
            
            # Verify final settings
            final_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            final_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            final_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            print(f"✅ TOPDON TC001 initialized at {final_width}x{final_height}@{final_fps}fps")
            
            # Update our internal settings to match actual camera
            self.width = final_width
            self.height = final_height
            self.fps = final_fps if final_fps > 0 else 25
            
            self.available = True
            return True
            
        except Exception as e:
            print(f"❌ Error initializing TOPDON TC001: {str(e)}")
            return False
    
    def find_camera_index(self):
        """Automatically find the correct camera index for TOPDON TC001"""
        print("Searching for TOPDON TC001 thermal camera...")
        
        # Try indices 0 through 10
        for index in range(11):
            try:
                test_cap = cv2.VideoCapture(index)
                if test_cap.isOpened():
                    # Test if this looks like a thermal camera
                    ret, frame = test_cap.read()
                    if ret and frame is not None:
                        h, w = frame.shape[:2]
                        # TOPDON TC001 can output 256x192 or 256x384
                        if (w == 256 and h in [192, 384]) or (w == 192 and h == 256):
                            test_cap.release()
                            print(f"✅ Found potential thermal camera at index {index} ({w}x{h})")
                            return index
                test_cap.release()
            except Exception as e:
                continue
        
        print("⚠️  No thermal camera found. Will try index 0 as fallback.")
        return 0
    
    def start_capture(self):
        """Start camera capture in background thread"""
        if not self.available:
            return False
            
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        return True
    
    def stop_capture(self):
        """Stop camera capture"""
        self.running = False
        if hasattr(self, 'capture_thread'):
            self.capture_thread.join(timeout=2)
        if self.cap:
            self.cap.release()
        # Clean up serial connections
        self.cleanup_serial()
    
    def _capture_loop(self):
        """Main capture loop"""
        print("🎥 Thermal camera capture loop started")
        while self.running and self.cap:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = self._process_thermal_frame(frame)
                    
                    # Send current measurement point temperature every second (if any)
                    current_time = time.time()
                    if (hasattr(self, 'custom_measurement_points') and self.custom_measurement_points and
                        current_time - self.last_measurement_send >= 1.0):
                        print(f"⏰ Time to send measurement data (last send: {current_time - self.last_measurement_send:.1f}s ago)")
                        self.send_measurement_to_teensy()
                        self.last_measurement_send = current_time
            
            # Send test data if test mode is enabled
            self._send_test_data_if_enabled()
            
            # Periodically check serial connection health
            self._check_serial_connections()
            
            time.sleep(1/25)  # 25 FPS
        print("🎥 Thermal camera capture loop stopped")
    
    def _process_thermal_frame(self, frame):
        """Process the thermal frame with enhanced temperature extraction"""
        try:
            # Ensure frame is valid and has proper dimensions
            if frame is None or frame.size == 0:
                print("Warning: Empty frame received")
                return self._create_error_frame("Empty Frame")
            
            # Debug frame information
            if hasattr(self, '_debug_frame_info') and self._frame_count % 60 == 0:
                print(f"Frame shape: {frame.shape}, dtype: {frame.dtype}")
            
            # Extract raw thermal data using Les Wright's method
            visual_frame, temperature_data = self._extract_raw_thermal_data(frame)
            
            # Convert to grayscale safely
            if visual_frame is not None:
                gray = self._safe_convert_to_grayscale(visual_frame)
            else:
                # Fallback to original frame processing
                gray = self._safe_convert_to_grayscale(frame)
            
            # Validate grayscale conversion
            if gray is None or gray.size == 0:
                print("Warning: Failed to convert to grayscale")
                return self._create_error_frame("Conversion Error")
            
            # Store raw thermal data for temperature analysis
            self.raw_thermal_data = temperature_data.copy() if temperature_data is not None else gray.copy()
            
            # Update frame counter for debugging
            self._frame_count = getattr(self, '_frame_count', 0) + 1
            
            # Debug: Log temperature range occasionally
            if self._frame_count % 30 == 0:
                min_temp = getattr(self, 'current_min_temp', 0)
                max_temp = getattr(self, 'current_max_temp', 0)
                print(f"🌡️  Temp range: {min_temp:.1f}°C to {max_temp:.1f}°C (dual-stream: {self.dual_stream_mode})")
            
            # Normalize the thermal data for better visualization
            normalized = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            
            # Apply advanced thermal processing
            processed = self._apply_thermal_processing(normalized)
            
            # Apply colormap for thermal visualization
            colored = cv2.applyColorMap(processed, self.colormap)
            
            # Scale the thermal image by 2x for better display (256x192 -> 512x384)
            colored = cv2.resize(colored, (colored.shape[1] * 2, colored.shape[0] * 2), interpolation=cv2.INTER_LINEAR)
            
            # Ensure the final image has 3 channels (BGR)
            colored = self._ensure_3_channels(colored)
            
            # Add temperature indicators with + symbols
            self._add_temperature_indicators(colored, gray)
            
            return colored
            
        except Exception as e:
            print(f"Error processing thermal frame: {str(e)}")
            return self._create_error_frame("Processing Error")
    
    def _safe_convert_to_grayscale(self, frame):
        """Safely convert frame to grayscale handling different channel formats"""
        try:
            if frame is None or frame.size == 0:
                return None
            
            # Check number of channels
            if len(frame.shape) == 2:
                # Already grayscale
                return frame.astype(np.uint8)
            elif len(frame.shape) == 3:
                channels = frame.shape[2]
                if channels == 1:
                    # Single channel in 3D format
                    return frame[:, :, 0].astype(np.uint8)
                elif channels == 3:
                    # BGR format
                    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                elif channels == 4:
                    # BGRA format
                    return cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
                elif channels == 2:
                    # Unexpected 2-channel format - use first channel
                    print(f"Warning: Unexpected 2-channel frame, using first channel")
                    return frame[:, :, 0].astype(np.uint8)
                else:
                    print(f"Warning: Unexpected {channels} channels, using first channel")
                    return frame[:, :, 0].astype(np.uint8)
            else:
                print(f"Warning: Unexpected frame dimensions: {frame.shape}")
                return None
                
        except Exception as e:
            print(f"Error converting to grayscale: {e}")
            return None
    
    def _ensure_3_channels(self, image):
        """Ensure image has exactly 3 channels (BGR format)"""
        try:
            if image is None or image.size == 0:
                return self._create_error_frame("Invalid Image")
            
            if len(image.shape) == 2:
                # Grayscale to BGR
                return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif len(image.shape) == 3:
                channels = image.shape[2]
                if channels == 1:
                    # Single channel in 3D format to BGR
                    gray = image[:, :, 0]
                    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                elif channels == 3:
                    # Already BGR
                    return image
                elif channels == 4:
                    # BGRA to BGR
                    return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
                else:
                    # Unexpected channels - use first 3
                    print(f"Warning: Unexpected {channels} channels, using first 3")
                    return image[:, :, :3]
            else:
                print(f"Warning: Cannot handle image shape: {image.shape}")
                return self._create_error_frame("Invalid Shape")
                
        except Exception as e:
            print(f"Error ensuring 3 channels: {e}")
            return self._create_error_frame("Channel Error")
    
    def _create_error_frame(self, error_message):
        """Create an error frame with a message"""
        try:
            # Create a black frame with error message at native resolution
            error_frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            
            # Add error text
            font = cv2.FONT_HERSHEY_SIMPLEX
            text_scale = 0.7
            text_color = (0, 0, 255)  # Red
            text_thickness = 2
            
            # Calculate text position
            text_size = cv2.getTextSize(error_message, font, text_scale, text_thickness)[0]
            text_x = (error_frame.shape[1] - text_size[0]) // 2
            text_y = (error_frame.shape[0] + text_size[1]) // 2
            
            cv2.putText(error_frame, error_message, (text_x, text_y), font, text_scale, text_color, text_thickness)
            
            # Scale the error frame by 2x to match display resolution
            error_frame = cv2.resize(error_frame, (error_frame.shape[1] * 2, error_frame.shape[0] * 2), interpolation=cv2.INTER_LINEAR)
            
            return error_frame
            
        except Exception as e:
            # Ultimate fallback - return a black frame at scaled resolution
            print(f"Error creating error frame: {e}")
            return np.zeros((384, 512, 3), dtype=np.uint8)  # 2x scaled fallback
    
    def _add_temperature_indicators(self, colored_frame, gray_frame):
        """Add temperature indicators with + symbols for hot and cold spots"""
        try:
            # Check if ROI is set and use it for min/max calculation
            if hasattr(self, 'roi_box') and self.roi_box is not None:
                roi_stats = self.get_roi_stats()
                if roi_stats:
                    # Use ROI for min/max values
                    min_temp_c = roi_stats['min_temp']
                    max_temp_c = roi_stats['max_temp']
                    
                    # Find min/max locations within ROI
                    roi_x1, roi_y1, roi_x2, roi_y2 = self.roi_box['x1'], self.roi_box['y1'], self.roi_box['x2'], self.roi_box['y2']
                    
                    # Clamp ROI to gray_frame bounds
                    roi_x1 = max(0, min(roi_x1, gray_frame.shape[1] - 1))
                    roi_y1 = max(0, min(roi_y1, gray_frame.shape[0] - 1))
                    roi_x2 = max(1, min(roi_x2, gray_frame.shape[1]))
                    roi_y2 = max(1, min(roi_y2, gray_frame.shape[0]))
                    
                    # Extract ROI from gray frame
                    roi_gray = gray_frame[roi_y1:roi_y2, roi_x1:roi_x2]
                    
                    if roi_gray.size > 0:
                        # Find min/max within ROI
                        roi_min_loc = np.unravel_index(np.argmin(roi_gray), roi_gray.shape)
                        roi_max_loc = np.unravel_index(np.argmax(roi_gray), roi_gray.shape)
                        
                        # Convert back to full frame coordinates
                        min_loc = (roi_min_loc[0] + roi_y1, roi_min_loc[1] + roi_x1)
                        max_loc = (roi_max_loc[0] + roi_y1, roi_max_loc[1] + roi_x1)
                    else:
                        # Fallback to full frame
                        min_loc = np.unravel_index(np.argmin(gray_frame), gray_frame.shape)
                        max_loc = np.unravel_index(np.argmax(gray_frame), gray_frame.shape)
                else:
                    # ROI stats failed, use full frame
                    min_loc = np.unravel_index(np.argmin(gray_frame), gray_frame.shape)
                    max_loc = np.unravel_index(np.argmax(gray_frame), gray_frame.shape)
                    min_temp_c = self.current_min_temp
                    max_temp_c = self.current_max_temp
            else:
                # No ROI set, use full frame
                min_loc = np.unravel_index(np.argmin(gray_frame), gray_frame.shape)
                max_loc = np.unravel_index(np.argmax(gray_frame), gray_frame.shape)
                
                # Use the actual temperature values if available
                if hasattr(self, 'temperature_data') and self.temperature_data is not None:
                    min_temp_c = self.current_min_temp
                    max_temp_c = self.current_max_temp
                else:
                    # Fallback to approximation from grayscale
                    min_val = np.min(gray_frame)
                    max_val = np.max(gray_frame)
                    temp_range = 80
                    base_temp = 10
                    min_temp_c = base_temp + (min_val / 255.0) * temp_range
                    max_temp_c = base_temp + (max_val / 255.0) * temp_range
            
            # Scale coordinates by 2x for the upscaled display
            min_loc = (min_loc[0] * 2, min_loc[1] * 2)
            max_loc = (max_loc[0] * 2, max_loc[1] * 2)
            
            # Draw + symbol for coldest point (blue)
            self._draw_plus_symbol(colored_frame, (min_loc[1], min_loc[0]), (255, 0, 0), 16)
            cv2.putText(colored_frame, f"MIN: {min_temp_c:.1f}C", 
                       (min_loc[1] + 30, min_loc[0] - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            # Draw + symbol for hottest point (red)
            self._draw_plus_symbol(colored_frame, (max_loc[1], max_loc[0]), (0, 0, 255), 16)
            cv2.putText(colored_frame, f"MAX: {max_temp_c:.1f}C", 
                       (max_loc[1] + 30, max_loc[0] + 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            # Draw custom measurement points
            if hasattr(self, 'custom_measurement_points') and self.custom_measurement_points:
                custom_temps = self.get_custom_point_temperatures()
                for temp_point in custom_temps:
                    x, y = temp_point['x'] * 2, temp_point['y'] * 2  # Scale coordinates by 2x
                    temp = temp_point['temperature']
                    point_id = temp_point['id']
                    
                    # Draw measurement point (purple circle) - scaled size
                    cv2.circle(colored_frame, (x, y), 6, (255, 0, 255), 4)
                    cv2.circle(colored_frame, (x, y), 2, (255, 255, 255), -1)
                    
                    # Add temperature text - scaled font
                    cv2.putText(colored_frame, f"P{point_id}: {temp:.1f}C", 
                               (x + 20, y - 20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
            
        except Exception as e:
            print(f"Error adding temperature indicators: {str(e)}")
    
    def _draw_plus_symbol(self, frame, center, color, size):
        """Draw a + symbol at the specified location"""
        try:
            x, y = center
            thickness = 2  # Increased thickness for scaled display
            
            # Draw horizontal line
            cv2.line(frame, (x - size, y), (x + size, y), color, thickness)
            # Draw vertical line
            cv2.line(frame, (x, y - size), (x, y + size), color, thickness)
            
            # Add small circle at center (scaled)
            cv2.circle(frame, (x, y), 2, color, -1)
            
        except Exception as e:
            print(f"Error drawing plus symbol: {str(e)}")
    
    def get_frame(self):
        """Get current frame for streaming"""
        with self.lock:
            return self.frame.copy() if self.frame is not None else None
    
    def get_status(self):
        """Get camera status"""
        # Check if we have real temperature data from Les Wright's method
        has_real_temp_data = hasattr(self, 'dual_stream_mode') and self.dual_stream_mode and hasattr(self, 'temperature_data')
        
        if has_real_temp_data:
            # Use real temperature data from Les Wright's method
            min_temp_c = self.current_min_temp
            max_temp_c = self.current_max_temp
            avg_temp_c = getattr(self, 'current_avg_temp', (min_temp_c + max_temp_c) / 2)
            center_temp_c = getattr(self, 'center_temperature', avg_temp_c)
            
            # Additional sanity check
            if min_temp_c < -50 or max_temp_c > 200:
                print(f"⚠️  Temperature values seem unrealistic: {min_temp_c:.1f}°C to {max_temp_c:.1f}°C")
        
        if not has_real_temp_data:
            # Use temperature data from approximation method
            if hasattr(self, 'temperature_data') and self.temperature_data is not None:
                min_temp_c = self.current_min_temp
                max_temp_c = self.current_max_temp
                avg_temp_c = self.current_avg_temp
                center_temp_c = getattr(self, 'center_temperature', avg_temp_c)
            else:
                # Fallback values
                min_temp_c = self.current_min_temp
                max_temp_c = self.current_max_temp
                avg_temp_c = self.current_avg_temp
                center_temp_c = avg_temp_c
        
        return {
            'available': self.available,
            'running': self.running,
            'camera_model': 'TOPDON TC001',
            'width': self.width,
            'height': self.height,
            'colormap': self._get_colormap_name(),
            'min_temperature': float(min_temp_c),
            'max_temperature': float(max_temp_c),
            'avg_temperature': float(avg_temp_c),
            'center_temperature': float(center_temp_c),
            'temperature_range': float(max_temp_c - min_temp_c),
            'temp_offset': float(getattr(self, 'temp_offset', 0.0)),
            'dual_stream_mode': getattr(self, 'dual_stream_mode', False),
            'real_temp_data': has_real_temp_data,
            'temp_data_source': "Les Wright's method" if has_real_temp_data else 'Linear approximation'
        }
    
    def _get_colormap_name(self):
        """Get colormap name"""
        colormap_map = {
            cv2.COLORMAP_INFERNO: 'inferno',
            cv2.COLORMAP_JET: 'jet',
            cv2.COLORMAP_HOT: 'hot',
            cv2.COLORMAP_COOL: 'cool',
        }
        return colormap_map.get(self.colormap, 'inferno')
    
    def change_colormap(self, colormap_name):
        """Change colormap"""
        colormap_map = {
            'inferno': cv2.COLORMAP_INFERNO,
            'jet': cv2.COLORMAP_JET,
            'hot': cv2.COLORMAP_HOT,
            'cool': cv2.COLORMAP_COOL,
        }
        if colormap_name in colormap_map:
            self.colormap = colormap_map[colormap_name]
            print(f"Colormap changed to {colormap_name}")
            return True
        return False

    def add_custom_measurement_point(self, x, y):
        """Add a custom measurement point at the specified coordinates"""
        try:
            # Scale coordinates back to native resolution (display is 2x scaled)
            native_x = int(x / 2)
            native_y = int(y / 2)
            
            # Validate coordinates against native resolution
            if not (0 <= native_x <= self.width and 0 <= native_y <= self.height):
                return False, f"Coordinates out of bounds: ({native_x}, {native_y})"
            
            # Add the measurement point using native coordinates
            point = {'x': native_x, 'y': native_y, 'id': len(self.custom_measurement_points) + 1}
            self.custom_measurement_points.append(point)
            
            print(f"Added custom measurement point at display ({x}, {y}) -> native ({native_x}, {native_y})")
            
            # Send the temperature immediately to the appropriate Teensy
            self.send_measurement_to_teensy()
            
            return True, f"Measurement point added at ({x}, {y})"
            
        except Exception as e:
            print(f"Error adding measurement point: {e}")
            return False, str(e)
    
    def clear_custom_measurement_points(self):
        """Clear all custom measurement points"""
        try:
            count = len(self.custom_measurement_points)
            self.custom_measurement_points.clear()
            print(f"Cleared {count} custom measurement points")
            return True, f"Cleared {count} measurement points"
            
        except Exception as e:
            print(f"Error clearing measurement points: {e}")
            return False, str(e)
    
    def get_custom_point_temperatures(self):
        """Get temperature readings for all custom measurement points"""
        print("🔍 get_custom_point_temperatures() called")
        temperatures = []
        
        if not self.custom_measurement_points or self.temperature_data is None:
            print(f"❌ No data - points: {len(self.custom_measurement_points) if hasattr(self, 'custom_measurement_points') and self.custom_measurement_points else 0}, temp_data: {'exists' if self.temperature_data is not None else 'None'}")
            return temperatures
        
        print(f"📍 Processing {len(self.custom_measurement_points)} points")
        
        try:
            for point in self.custom_measurement_points:
                x, y = point['x'], point['y']
                
                # Use coordinates directly
                orig_x, orig_y = x, y
                
                # Ensure coordinates are within bounds
                orig_x = max(0, min(orig_x, self.temperature_data.shape[1] - 1))
                orig_y = max(0, min(orig_y, self.temperature_data.shape[0] - 1))
                
                # Get temperature at this point
                temp = self.temperature_data[orig_y, orig_x]
                
                print(f"🌡️ Point ({x}, {y}) -> bounded ({orig_x}, {orig_y}) = {temp:.1f}°C")
                
                temperatures.append({
                    'id': point['id'],
                    'x': x,
                    'y': y,
                    'temperature': float(temp)
                })
                
        except Exception as e:
            print(f"Error getting custom point temperatures: {e}")
        
        return temperatures

    def set_roi(self, x1, y1, x2, y2):
        """Set Region of Interest for temperature analysis"""
        try:
            # Scale coordinates back to native resolution (display is 2x scaled)
            native_x1 = int(x1 / 2)
            native_y1 = int(y1 / 2)
            native_x2 = int(x2 / 2)
            native_y2 = int(y2 / 2)
            
            # Validate coordinates against native resolution
            max_width = self.width
            max_height = self.height
            
            if not (0 <= native_x1 < native_x2 <= max_width and 0 <= native_y1 < native_y2 <= max_height):
                return False, f"Invalid ROI coordinates: ({native_x1}, {native_y1}) to ({native_x2}, {native_y2})"
            
            # Store ROI using native coordinates
            self.roi_box = {
                'x1': native_x1,
                'y1': native_y1, 
                'x2': native_x2,
                'y2': native_y2
            }
            
            print(f"ROI set: display ({x1}, {y1}) to ({x2}, {y2}) -> native ({native_x1}, {native_y1}) to ({native_x2}, {native_y2})")
            return True, f"ROI set: ({x1}, {y1}) to ({x2}, {y2})"
            
        except Exception as e:
            print(f"Error setting ROI: {e}")
            return False, str(e)
    
    def clear_roi(self):
        """Clear Region of Interest"""
        try:
            self.roi_box = None
            print("ROI cleared")
            return True, "ROI cleared"
            
        except Exception as e:
            print(f"Error clearing ROI: {e}")
            return False, str(e)
    
    def get_roi_stats(self):
        """Get temperature statistics for the current ROI"""
        if self.roi_box is None or self.temperature_data is None:
            return None
        
        try:
            # Use ROI coordinates directly
            x1, y1, x2, y2 = self.roi_box['x1'], self.roi_box['y1'], self.roi_box['x2'], self.roi_box['y2']
            
            # Ensure coordinates are within bounds
            x1 = max(0, min(x1, self.temperature_data.shape[1] - 1))
            y1 = max(0, min(y1, self.temperature_data.shape[0] - 1))
            x2 = max(1, min(x2, self.temperature_data.shape[1]))
            y2 = max(1, min(y2, self.temperature_data.shape[0]))
            
            # Extract ROI region
            roi_data = self.temperature_data[y1:y2, x1:x2]
            
            if roi_data.size == 0:
                return None
            
            return {
                'min_temp': float(np.min(roi_data)),
                'max_temp': float(np.max(roi_data)),
                'avg_temp': float(np.mean(roi_data)),
                'roi_coords': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}
            }
            
        except Exception as e:
            print(f"Error getting ROI stats: {e}")
            return None

    def _extract_raw_thermal_data(self, frame):
        """Extract raw thermal data from the camera frame using Les Wright's proven method"""
        try:
            # Validate input frame
            if frame is None or frame.size == 0:
                return None, None
            
            # Debug frame information occasionally
            if getattr(self, '_frame_count', 0) % 60 == 0:
                print(f"Input frame shape: {frame.shape}, dtype: {frame.dtype}")
            
            # Check if we have the dual-stream format (256x384)
            if frame.shape[0] == 384 and frame.shape[1] == 256:
                # Log detection only once to avoid spam
                if not hasattr(self, '_dual_stream_detected'):
                    print(f"Dual-stream format detected ({frame.shape[1]}x{frame.shape[0]}), using Les Wright's temperature extraction")
                    self._dual_stream_detected = True
                    self.dual_stream_mode = True
                
                # Split frame into image and thermal data (Les Wright's method)
                imdata, thdata = np.array_split(frame, 2)
                
                # Extract temperature from center pixel
                hi = int(thdata[96][128][0])
                lo = int(thdata[96][128][1])
                lo = lo * 256
                rawtemp = hi + lo
                center_temp = (rawtemp / 64) - 273.15
                center_temp = round(center_temp, 2)
                
                # Find max temperature in the frame
                lomax = int(thdata[..., 1].max())
                posmax = thdata[..., 1].argmax()
                mcol, mrow = divmod(posmax, 256)  # width = 256
                himax = int(thdata[mcol][mrow][0])
                lomax = lomax * 256
                maxtemp = himax + lomax
                max_temp = (maxtemp / 64) - 273.15
                max_temp = round(max_temp, 2)
                
                # Find min temperature in the frame
                lomin = int(thdata[..., 1].min())
                posmin = thdata[..., 1].argmin()
                lcol, lrow = divmod(posmin, 256)  # width = 256
                himin = int(thdata[lcol][lrow][0])
                lomin = lomin * 256
                mintemp = himin + lomin
                min_temp = (mintemp / 64) - 273.15
                min_temp = round(min_temp, 2)
                
                # Find average temperature
                loavg = float(thdata[..., 1].mean())
                hiavg = float(thdata[..., 0].mean())
                loavg = loavg * 256
                avgtemp = loavg + hiavg
                avg_temp = (avgtemp / 64) - 273.15
                avg_temp = round(avg_temp, 2)
                
                # Store temperature statistics
                self.current_min_temp = min_temp
                self.current_max_temp = max_temp
                self.current_avg_temp = avg_temp
                self.center_temperature = center_temp
                
                # Create temperature data array for compatibility with existing code
                # Use the thermal data part for temperature calculations
                temperature_data = np.zeros_like(thdata[:, :, 0], dtype=np.float32)
                
                # Calculate temperature for each pixel using Les Wright's method
                for y in range(thdata.shape[0]):
                    for x in range(thdata.shape[1]):
                        hi_val = int(thdata[y, x, 0])
                        lo_val = int(thdata[y, x, 1])
                        lo_val = lo_val * 256
                        raw_val = hi_val + lo_val
                        temperature_data[y, x] = (raw_val / 64) - 273.15
                
                # Store raw thermal data for compatibility
                self.raw_thermal_data = temperature_data
                self.temperature_data = temperature_data
                
                print(f"Les Wright temperature extraction - Min: {min_temp:.1f}°C, Max: {max_temp:.1f}°C, Avg: {avg_temp:.1f}°C, Center: {center_temp:.1f}°C")
                
                # Convert the real image to BGR (Les Wright's method)
                visual_frame = cv2.cvtColor(imdata, cv2.COLOR_YUV2BGR_YUYV)
                
                return visual_frame, temperature_data
                
            else:
                # Standard mode: use approximation method
                if not hasattr(self, '_single_stream_detected'):
                    print(f"Single stream format detected ({frame.shape[1]}x{frame.shape[0]}), using approximation method")
                    self._single_stream_detected = True
                    self.dual_stream_mode = False
                
                gray = self._safe_convert_to_grayscale(frame)
                
                if gray is not None:
                    temperature_data = self._approximate_temperature_from_grayscale(gray)
                    return frame, temperature_data
                else:
                    print("Warning: Failed to convert frame to grayscale")
                    return frame, None
                
        except Exception as e:
            # Log error only once to avoid spam
            if not hasattr(self, '_thermal_extraction_error_logged'):
                print(f"Error extracting thermal data: {e}")
                self._thermal_extraction_error_logged = True
            return frame, None
    
    def _convert_raw_to_temperature(self, thermal_gray):
        """Convert raw thermal data to temperature using Les Wright's method"""
        try:
            # TOPDON TC001 specific temperature conversion
            # Based on Les Wright's analysis, the raw values map to temperature
            
            # Apply calibration offset
            temp_offset = getattr(self, 'temp_offset', 0.0)
            
            # Convert raw pixel values to temperature
            # This is camera-specific and may need calibration
            min_temp_range = -10.0  # Minimum temperature the camera can detect
            max_temp_range = 120.0  # Maximum temperature the camera can detect
            
            # Normalize raw values (0-255) to temperature range
            normalized = thermal_gray.astype(np.float32) / 255.0
            temperature_data = min_temp_range + normalized * (max_temp_range - min_temp_range) + temp_offset
            
            # Calculate temperature statistics
            self.current_min_temp = np.min(temperature_data)
            self.current_max_temp = np.max(temperature_data)
            self.current_avg_temp = np.mean(temperature_data)
            
            # Get center temperature (crosshair)
            center_y, center_x = temperature_data.shape[0] // 2, temperature_data.shape[1] // 2
            self.center_temperature = temperature_data[center_y, center_x]
            
            return temperature_data
            
        except Exception as e:
            print(f"Error converting raw to temperature: {e}")
            return thermal_gray.astype(np.float32)
    
    def _approximate_temperature_from_grayscale(self, gray_frame):
        """
        Approximate temperature from grayscale values when dual-stream mode is not available.
        This is less accurate but provides reasonable temperature estimates.
        """
        try:
            # Convert grayscale values to temperature using linear approximation
            # Use more reasonable temperature range for typical thermal imaging: 0°C to 100°C
            min_temp = 0.0
            max_temp = 100.0
            
            # Apply user calibration offset
            temp_offset = getattr(self, 'temp_offset', 0.0)
            
            # Normalize grayscale values to temperature range
            # Assume room temperature (20°C) at mid-range grayscale values
            normalized = gray_frame.astype(np.float32) / 255.0
            
            # Map to temperature range with room temperature bias
            room_temp = 20.0
            temperature_data = room_temp + (normalized - 0.5) * (max_temp - min_temp) * 0.8 + temp_offset
            
            # Clamp to reasonable range
            temperature_data = np.clip(temperature_data, min_temp, max_temp)
            
            # Store temperature statistics
            self.current_min_temp = np.min(temperature_data)
            self.current_max_temp = np.max(temperature_data)
            self.current_avg_temp = np.mean(temperature_data)
            
            # Get center temperature (crosshair)
            center_y, center_x = gray_frame.shape[0] // 2, gray_frame.shape[1] // 2
            self.center_temperature = temperature_data[center_y, center_x]
            
            return temperature_data
            
        except Exception as e:
            print(f"Error in temperature approximation: {e}")
            return gray_frame.astype(np.float32)
    
    def _apply_thermal_processing(self, frame):
        """Apply thermal-specific processing for better visualization"""
        try:
            # Apply gamma correction for better thermal visualization
            gamma = 0.8
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            gamma_corrected = cv2.LUT(frame, table)
            
            # Apply slight gaussian blur for smoother thermal visualization
            smoothed = cv2.GaussianBlur(gamma_corrected, (3, 3), 0)
            
            return smoothed
            
        except Exception as e:
            print(f"Error in thermal processing: {str(e)}")
            return frame
def check_system_status():
    """Check if the DryBox system is running by looking for required processes."""
    try:
        # Check if JSONparse.py, serialDebug.py and logDB.py are running
        jsonparse_running = subprocess.run(
            ["pgrep", "-f", "python3 .*/JSONparse.py"], 
            capture_output=True
        ).stdout.strip()
        
        serialdebug_running = subprocess.run(
            ["pgrep", "-f", "python3 .*/serialDebug.py"], 
            capture_output=True
        ).stdout.strip()
        
        logdb_running = subprocess.run(
            ["pgrep", "-f", "python3 .*/logDB.py"], 
            capture_output=True
        ).stdout.strip()
        
        # System is running if all three processes are active
        return bool(jsonparse_running and serialdebug_running and logdb_running)
    except Exception as e:
        print(f"Error checking system status: {e}")
        return False

def update_system_state():
    """Update the global system state variables."""
    global system_running
    system_running = check_system_status()

# Initialize system state on startup
update_system_state()

# Create DataLogging directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

@app.route('/')
def index():
    """Render the main web interface."""
    update_system_state()
    
    # Get log file content (last 50 lines)
    startup_log = get_log_content(STARTUP_LOG, 50)
    shutdown_log = get_log_content(SHUTDOWN_LOG, 50)
    jsonparse_log = get_log_content(JSONPARSE_LOG, 50)
    serialdebug_log = get_log_content(SERIALDEBUG_LOG, 50)
    
    return render_template('index.html', 
                          system_running=system_running,
                          last_action=last_action,
                          last_action_time=last_action_time,
                          startup_log=startup_log,
                          shutdown_log=shutdown_log,
                          jsonparse_log=jsonparse_log,
                          serialdebug_log=serialdebug_log)

@app.route('/debug')
def debug():
    """Render the debug panel interface."""
    update_system_state()
    
    # Get log file content (last 50 lines) for initial display
    startup_log = get_log_content(STARTUP_LOG, 50)
    shutdown_log = get_log_content(SHUTDOWN_LOG, 50)
    jsonparse_log = get_log_content(JSONPARSE_LOG, 50)
    serialdebug_log = get_log_content(SERIALDEBUG_LOG, 50)
    flash_log = get_log_content(FLASH_LOG, 50)
    
    return render_template('debug.html', 
                          system_running=system_running,
                          startup_log=startup_log,
                          shutdown_log=shutdown_log,
                          jsonparse_log=jsonparse_log,
                          serialdebug_log=serialdebug_log,
                          flash_log=flash_log)

def get_log_content(log_path, num_lines=50):
    """Read the last n lines from a log file."""
    if not os.path.exists(log_path):
        return "Log file not found."
    
    try:
        result = subprocess.run(
            ["tail", "-n", str(num_lines), log_path], 
            capture_output=True, 
            text=True
        )
        return result.stdout
    except Exception as e:
        return f"Error reading log file: {e}"

@app.route('/api/start', methods=['POST'])
def start_system():
    """API endpoint to start the DryBox system."""
    global last_action, last_action_time, system_running
    
    if system_running:
        return jsonify({"status": "error", "message": "System is already running"})
    
    try:
        # Execute the start script
        result = subprocess.run(
            ["bash", START_SCRIPT], 
            capture_output=True, 
            text=True
        )
        
        # Update status
        time.sleep(3)  # Give processes time to start
        update_system_state()
        
        last_action = "start"
        last_action_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if system_running:
            return jsonify({
                "status": "success", 
                "message": "DryBox system started successfully",
                "output": result.stdout,
                "system_running": system_running
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Failed to start DryBox system",
                "output": result.stdout + "\n" + result.stderr,
                "system_running": system_running
            })
    
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Error starting DryBox system: {str(e)}",
            "system_running": check_system_status()
        })

@app.route('/api/stop', methods=['POST'])
def stop_system():
    """API endpoint to stop the DryBox system."""
    global last_action, last_action_time, system_running
    
    if not system_running:
        return jsonify({"status": "error", "message": "System is not running"})
    
    try:
        # Get stop parameters
        force_stop = request.json.get('force', False)
        ensure_alloff = request.json.get('ensure_alloff', True)
        timeout = request.json.get('timeout', 3)
        
        # Build command arguments
        cmd = ["bash", STOP_SCRIPT]
        if force_stop:
            cmd.append("--force")
        if ensure_alloff:
            cmd.append("--ensure-alloff")
        if timeout != 15:
            cmd.append(f"--timeout={timeout}")
        
        # Execute the stop script
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Update status
        time.sleep(3)  # Give processes time to stop
        update_system_state()
        
        last_action = "stop"
        last_action_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return jsonify({
            "status": "success", 
            "message": "DryBox system stop command executed",
            "output": result.stdout,
            "system_running": system_running
        })
    
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Error stopping DryBox system: {str(e)}",
            "system_running": check_system_status()
        })

@app.route('/api/status')
def get_status():
    """API endpoint to get the current system status."""
    update_system_state()
    return jsonify({
        "system_running": system_running,
        "last_action": last_action,
        "last_action_time": last_action_time
    })

@app.route('/api/logs/<log_type>')
def get_logs(log_type):
    """API endpoint to get log file content."""
    num_lines = request.args.get('lines', 50, type=int)
    
    if log_type == 'startup':
        log_content = get_log_content(STARTUP_LOG, num_lines)
    elif log_type == 'shutdown':
        log_content = get_log_content(SHUTDOWN_LOG, num_lines)
    elif log_type == 'jsonparse':
        log_content = get_log_content(JSONPARSE_LOG, num_lines)
    elif log_type == 'serialdebug':
        log_content = get_log_content(SERIALDEBUG_LOG, num_lines)
    elif log_type == 'flash':
        log_content = get_log_content(FLASH_LOG, num_lines)
    else:
        return jsonify({"status": "error", "message": "Invalid log type"})
    
    return jsonify({
        "status": "success",
        "content": log_content
    })

@app.route('/api/flash', methods=['POST'])
def flash_teensy():
    """API endpoint to flash Teensy microcontrollers."""
    target = request.json.get('target', 'all')
    
    # Check if target is valid
    valid_targets = ['TeensyHVAC', 'TeensyLeft', 'TeensyRight', 'all']
    if target not in valid_targets:
        return jsonify({
            "status": "error",
            "message": f"Invalid target: {target}. Valid targets are: {', '.join(valid_targets)}"
        })
    
    try:
        # Execute the flash script asynchronously
        def run_flash_script():
            subprocess.run(["bash", FLASH_SCRIPT, target], check=True)
        
        threading.Thread(target=run_flash_script).start()
        
        return jsonify({
            "status": "success",
            "message": f"Flash operation started for {target}. Check flash log for progress."
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error flashing Teensy: {str(e)}"
        })

@app.route('/stream_flash_log')
def stream_flash_log():
    """Stream flash log file content in real-time."""
    def generate():
        if not os.path.exists(FLASH_LOG):
            yield "Flash log file not found. It will be created when you start a flash operation.\n"
            return
        
        # First yield the existing content
        with open(FLASH_LOG, 'r') as f:
            content = f.read()
            yield content
            
            # Then continue to yield new content as it's added
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                yield line
    
    return Response(stream_with_context(generate()), mimetype='text/plain')

@app.route('/stream_log/<log_type>')
def stream_log(log_type):
    """Stream log file content in real-time."""
    if log_type == 'startup':
        log_path = STARTUP_LOG
    elif log_type == 'shutdown':
        log_path = SHUTDOWN_LOG
    elif log_type == 'jsonparse':
        log_path = JSONPARSE_LOG
    elif log_type == 'serialdebug':
        log_path = SERIALDEBUG_LOG
    else:
        return "Invalid log type", 400
    
    def generate():
        if not os.path.exists(log_path):
            yield "Log file not found.\n"
            return
        
        # First yield the existing content
        with open(log_path, 'r') as f:
            content = f.read()
            yield content
            
            # Then continue to yield new content as it's added
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                yield line
    
    return Response(generate(), mimetype='text/plain')

@app.route('/api/upload_shell_json', methods=['POST'])
def upload_shell_json():
    """API endpoint to upload a new shellJson.json file."""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"})
    
    try:
        # Read the uploaded file content
        file_content = file.read().decode('utf-8')
        
        # Validate JSON format
        try:
            json_data = json.loads(file_content)
        except json.JSONDecodeError as e:
            return jsonify({
                "status": "error", 
                "message": f"Invalid JSON format: {str(e)}"
            })
        
        # Validate against schema if schema file exists
        if os.path.exists(SCHEMA_FILE):
            try:
                with open(SCHEMA_FILE, 'r') as schema_file:
                    schema = json.load(schema_file)
                jsonschema.validate(instance=json_data, schema=schema)
            except json.JSONDecodeError as e:
                # If schema file is not valid JSON, log the error but continue
                print(f"Warning: Schema file is not valid JSON: {str(e)}")
            except jsonschema.exceptions.ValidationError as e:
                return jsonify({
                    "status": "error", 
                    "message": f"JSON validation failed: {str(e)}"
                })
        
        # Create backup of existing file (delete old backups first)
        if os.path.exists(SHELL_JSON):
            # Delete any existing backup files
            backup_pattern = f"{SHELL_JSON}.bak.*"
            for old_backup in glob.glob(backup_pattern):
                try:
                    os.remove(old_backup)
                    print(f"Deleted old backup: {old_backup}")
                except Exception as e:
                    print(f"Warning: Could not delete old backup {old_backup}: {e}")
            
            # Create new backup
            backup_path = f"{SHELL_JSON}.bak.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            shutil.copy2(SHELL_JSON, backup_path)
        
        # Write the new JSON file
        with open(SHELL_JSON, 'w') as f:
            f.write(file_content)
        
        # Log the action
        global last_action, last_action_time
        last_action = "upload_shell_json"
        last_action_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if the system is running and we need to restart JSONparse.py
        restart_needed = system_running
        restart_message = ""
        
        if restart_needed:
            restart_message = " You may need to restart the DryBox system for changes to take effect."
        
        return jsonify({
            "status": "success", 
            "message": f"shellJson.json uploaded successfully.{restart_message}",
            "restart_needed": restart_needed
        })
    
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Error uploading shellJson.json: {str(e)}"
        })

@app.route('/api/get_shell_json')
def get_shell_json():
    """API endpoint to get the current shellJson.json file content."""
    try:
        if not os.path.exists(SHELL_JSON):
            return jsonify({
                "status": "error",
                "message": "shellJson.json file not found"
            })
        
        with open(SHELL_JSON, 'r') as f:
            content = f.read()
        
        return jsonify({
            "status": "success",
            "content": content
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error reading shellJson.json: {str(e)}"
        })

@app.route('/api/get_current_layer')
def get_current_layer():
    """API endpoint to get the current active shell layer."""
    try:
        # This information will be stored in a file that JSONparse.py updates
        layer_info_file = CURRENT_LAYER_INFO
        
        if not os.path.exists(layer_info_file):
            return jsonify({
                "status": "error",
                "message": "Layer information not available",
                "current_layer": 0,
                "total_layers": 0,
                "layer_name": "Unknown",
                "current_step": 0,
                "total_steps": 0,
                "is_idle": False
            })
        
        with open(layer_info_file, 'r') as f:
            content = f.read().strip().split(',')
            if len(content) >= 5:
                current_layer = int(content[0])
                total_layers = int(content[1])
                layer_name = content[2]
                current_step = int(content[3])
                total_steps = int(content[4])
                
                # Parse elapsed and remaining time if available
                elapsed_time = 0
                remaining_time = 0
                if len(content) >= 7:
                    try:
                        elapsed_time = int(content[5])
                        remaining_time = int(content[6])
                    except (ValueError, IndexError):
                        pass
                
                # Check if we're in idle state
                is_idle = (layer_name == "IDLE")
                
                return jsonify({
                    "status": "success",
                    "current_layer": current_layer,
                    "total_layers": total_layers,
                    "layer_name": layer_name,
                    "current_step": current_step,
                    "total_steps": total_steps,
                    "elapsed_time": elapsed_time,
                    "remaining_time": remaining_time,
                    "is_idle": is_idle
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": "Invalid layer information format",
                    "current_layer": 0,
                    "total_layers": 0,
                    "layer_name": "Unknown",
                    "current_step": 0,
                    "total_steps": 0,
                    "elapsed_time": 0,
                    "remaining_time": 0,
                    "is_idle": False
                })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error getting current layer: {str(e)}",
            "current_layer": 0,
            "total_layers": 0,
            "layer_name": "Unknown",
            "current_step": 0,
            "total_steps": 0,
            "elapsed_time": 0,
            "remaining_time": 0,
            "is_idle": False
        })

@app.route('/api/next_layer', methods=['POST'])
def next_layer():
    """API endpoint to advance to the next shell layer."""
    if not system_running:
        return jsonify({
            "status": "error",
            "message": "DryBox system is not running"
        })
    
    try:
        # Create a trigger file that JSONparse.py will detect
        with open(NEXT_LAYER_TRIGGER, 'w') as f:
            f.write(str(datetime.datetime.now()))
        
        return jsonify({
            "status": "success",
            "message": "Next layer command sent"
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error advancing to next layer: {str(e)}"
        })

@app.route('/api/prev_layer', methods=['POST'])
def prev_layer():
    """API endpoint to go back to the previous shell layer."""
    if not system_running:
        return jsonify({
            "status": "error",
            "message": "DryBox system is not running"
        })
    
    try:
        # Create a trigger file that JSONparse.py will detect
        with open(PREV_LAYER_TRIGGER, 'w') as f:
            f.write(str(datetime.datetime.now()))
        
        return jsonify({
            "status": "success",
            "message": "Previous layer command sent"
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error going to previous layer: {str(e)}"
        })

@app.route('/api/jump_to_layer', methods=['POST'])
def jump_to_layer():
    """API endpoint to jump to a specific shell layer."""
    if not system_running:
        return jsonify({
            "status": "error",
            "message": "DryBox system is not running"
        })
    
    try:
        # Get the target layer from the request
        target_layer = request.json.get('target_layer', 1)
        
        # Validate the target layer (must be a positive integer)
        if not isinstance(target_layer, int) or target_layer < 1:
            return jsonify({
                "status": "error",
                "message": "Invalid target layer. Must be a positive integer."
            })
        
        # Create a trigger file that JSONparse.py will detect
        with open(JUMP_TO_LAYER_TRIGGER, 'w') as f:
            f.write(str(target_layer))
        
        return jsonify({
            "status": "success",
            "message": f"Jump to layer {target_layer} command sent"
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error jumping to layer: {str(e)}"
        })

@app.route('/api/next_step', methods=['POST'])
def next_step():
    """API endpoint to advance to the next step within the current layer."""
    if not system_running:
        return jsonify({
            "status": "error",
            "message": "DryBox system is not running"
        })
    
    try:
        # Create a trigger file that JSONparse.py will detect
        with open(NEXT_STEP_TRIGGER, 'w') as f:
            f.write(str(datetime.datetime.now()))
        
        return jsonify({
            "status": "success",
            "message": "Next step command sent"
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error advancing to next step: {str(e)}"
        })

@app.route('/api/prev_step', methods=['POST'])
def prev_step():
    """API endpoint to go back to the previous step within the current layer."""
    if not system_running:
        return jsonify({
            "status": "error",
            "message": "DryBox system is not running"
        })
    
    try:
        # Create a trigger file that JSONparse.py will detect
        with open(PREV_STEP_TRIGGER, 'w') as f:
            f.write(str(datetime.datetime.now()))
        
        return jsonify({
            "status": "success",
            "message": "Previous step command sent"
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error going to previous step: {str(e)}"
        })

@app.route('/api/set_idle_config', methods=['POST'])
def set_idle_config():
    """API endpoint to configure idle state parameters after layers complete."""
    try:
        idle_config = request.json
        
        # Validate required fields
        required_fields = ['ambient_temperature', 'shell_temperature', 'humidity', 'shell_speed', 'fan_speed']
        for field in required_fields:
            if field not in idle_config:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                })
        
        # Create idle configuration file
        # Save temperatures in Celsius (no conversion needed)
        with open(IDLE_CONFIG_PATH, 'w') as f:
            json.dump(idle_config, f, indent=2)
        
        return jsonify({
            "status": "success",
            "message": "Idle configuration saved successfully"
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error saving idle configuration: {str(e)}"
        })

@app.route('/api/get_idle_config')
def get_idle_config():
    """API endpoint to get the current idle configuration."""
    try:
        if not os.path.exists(IDLE_CONFIG_PATH):
            # Return default idle configuration
            default_config = {
                "ambient_temperature": 26,  # Celsius
                "shell_temperature": 0,    # Celsius
                "humidity": 0,             # %
                "shell_speed": 0,          # RPM
                "fan_speed": 0             # CFM
            }
            return jsonify({
                "status": "success",
                "config": default_config
            })
        
        with open(IDLE_CONFIG_PATH, 'r') as f:
            config = json.load(f)
            
        # Temperatures are already stored in Celsius, no conversion needed
        return jsonify({
            "status": "success",
            "config": config
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error reading idle configuration: {str(e)}"
        })

# ========================
# THERMAL CAMERA ROUTES
# ========================

def generate_thermal_frames():
    """Generate frames for thermal camera video stream"""
    try:
        while True:
            if thermal_camera and thermal_camera.available:
                frame = thermal_camera.get_frame()
                if frame is not None:
                    try:
                        # Encode frame as JPEG
                        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                        if ret:
                            frame_bytes = buffer.tobytes()
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    except Exception as e:
                        print(f"Error encoding thermal frame: {e}")
            else:
                # Send placeholder image when camera not available
                try:
                    placeholder = np.zeros((384, 512, 3), dtype=np.uint8)  # 2x scaled resolution
                    cv2.putText(placeholder, "Thermal Camera", (40, 192), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 4)
                    cv2.putText(placeholder, "Not Available", (60, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 4)
                    ret, buffer = cv2.imencode('.jpg', placeholder, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                except:
                    pass
            time.sleep(1/15)  # 15 FPS for thermal
    except GeneratorExit:
        # Handle client disconnect gracefully
        print("🔌 Thermal feed client disconnected")
        return
    except Exception as e:
        print(f"❌ Error in thermal frame generation: {e}")
        return



@app.route('/thermal_feed')
def thermal_feed():
    """Thermal camera video stream"""
    return Response(stream_with_context(generate_thermal_frames()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/thermal/status')
def thermal_status():
    """Get thermal camera status"""
    if thermal_camera:
        return jsonify(thermal_camera.get_status())
    else:
        return jsonify({
            'available': False,
            'running': False,
            'error': 'Thermal camera not initialized'
        })

@app.route('/api/thermal/start', methods=['POST'])
def start_thermal():
    """Start thermal camera"""
    global thermal_camera
    
    if not THERMAL_CAMERA_AVAILABLE:
        return jsonify({
            "status": "error", 
            "message": "OpenCV not available. Install with: pip install opencv-python"
        })
    
    try:
        if not thermal_camera:
            thermal_camera = ThermalCamera()
        
        if thermal_camera.initialize_camera():
            if thermal_camera.start_capture():
                return jsonify({
                    "status": "success",
                    "message": "Thermal camera started successfully"
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": "Failed to start thermal camera capture"
                })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to initialize thermal camera"
            })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error starting thermal camera: {str(e)}"
        })

@app.route('/api/thermal/stop', methods=['POST'])
def stop_thermal():
    """Stop thermal camera"""
    global thermal_camera
    
    try:
        if thermal_camera:
            thermal_camera.stop_capture()
            return jsonify({
                "status": "success",
                "message": "Thermal camera stopped"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Thermal camera not running"
            })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error stopping thermal camera: {str(e)}"
        })

@app.route('/api/thermal/colormap/<colormap_name>')
def change_thermal_colormap(colormap_name):
    """Change thermal colormap"""
    if thermal_camera and thermal_camera.available:
        success = thermal_camera.change_colormap(colormap_name)
        return jsonify({
            'success': success, 
            'colormap': colormap_name
        })
    else:
        return jsonify({
            'success': False, 
            'error': 'Thermal camera not available'
        })

@app.route('/api/thermal/temperature')
def get_thermal_temperature():
    """Get current temperature readings"""
    if thermal_camera and thermal_camera.available:
        status = thermal_camera.get_status()
        return jsonify({
            'min_temperature': status['min_temperature'],
            'max_temperature': status['max_temperature'],
            'avg_temperature': status['avg_temperature'],
            'unit': 'celsius'
        })
    else:
        return jsonify({
            'error': 'Thermal camera not available'
        })

@app.route('/api/thermal/add_custom_point', methods=['POST'])
def add_custom_thermal_point():
    """Add a custom temperature measurement point"""
    if not thermal_camera or not thermal_camera.available:
        return jsonify({
            'success': False,
            'error': 'Thermal camera not available'
        })
    
    try:
        data = request.get_json()
        if not data or 'x' not in data or 'y' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing x or y coordinates'
            })
        
        x = data['x']
        y = data['y']
        
        success, message = thermal_camera.add_custom_measurement_point(x, y)
        
        return jsonify({
            'success': success,
            'message': message,
            'point': {'x': x, 'y': y} if success else None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error adding measurement point: {str(e)}'
        })

@app.route('/api/thermal/clear_custom_points', methods=['POST'])
def clear_custom_thermal_points():
    """Clear all custom temperature measurement points"""
    if not thermal_camera or not thermal_camera.available:
        return jsonify({
            'success': False,
            'error': 'Thermal camera not available'
        })
    
    try:
        success, message = thermal_camera.clear_custom_measurement_points()
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error clearing measurement points: {str(e)}'
        })

@app.route('/api/thermal/custom_points')
def get_custom_thermal_points():
    """Get all custom measurement points and their temperatures"""
    if not thermal_camera or not thermal_camera.available:
        return jsonify({
            'success': False,
            'error': 'Thermal camera not available'
        })
    
    try:
        points = thermal_camera.get_custom_point_temperatures()
        
        return jsonify({
            'success': True,
            'points': points
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting measurement points: {str(e)}'
        })

@app.route('/api/thermal/set_roi', methods=['POST'])
def set_thermal_roi():
    """Set Region of Interest for thermal analysis"""
    if not thermal_camera or not thermal_camera.available:
        return jsonify({
            'success': False,
            'error': 'Thermal camera not available'
        })
    
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ['x1', 'y1', 'x2', 'y2']):
            return jsonify({
                'success': False,
                'error': 'Missing ROI coordinates (x1, y1, x2, y2)'
            })
        
        x1, y1, x2, y2 = data['x1'], data['y1'], data['x2'], data['y2']
        
        success, message = thermal_camera.set_roi(x1, y1, x2, y2)
        
        return jsonify({
            'success': success,
            'message': message,
            'roi': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2} if success else None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error setting ROI: {str(e)}'
        })

@app.route('/api/thermal/clear_roi', methods=['POST'])
def clear_thermal_roi():
    """Clear Region of Interest for thermal analysis"""
    if not thermal_camera or not thermal_camera.available:
        return jsonify({
            'success': False,
            'error': 'Thermal camera not available'
        })
    
    try:
        success, message = thermal_camera.clear_roi()
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error clearing ROI: {str(e)}'
        })

@app.route('/api/thermal/roi_stats')
def get_thermal_roi_stats():
    """Get temperature statistics for current ROI"""
    if not thermal_camera or not thermal_camera.available:
        return jsonify({
            'success': False,
            'error': 'Thermal camera not available'
        })
    
    try:
        roi_stats = thermal_camera.get_roi_stats()
        
        if roi_stats:
            return jsonify({
                'success': True,
                'roi_active': True,
                'stats': roi_stats
            })
        else:
            return jsonify({
                'success': True,
                'roi_active': False,
                'message': 'No ROI set'
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting ROI stats: {str(e)}'
        })

@app.route('/api/thermal/test_mode/enable', methods=['POST'])
def enable_thermal_test_mode():
    """Enable thermal test mode with static temperature"""
    if not thermal_camera or not thermal_camera.available:
        return jsonify({
            'success': False,
            'error': 'Thermal camera not available'
        })
    
    try:
        data = request.get_json() or {}
        temperature = data.get('temperature', 42.5)
        
        thermal_camera.enable_test_mode(temperature)
        
        return jsonify({
            'success': True,
            'message': f'Test mode enabled - sending {temperature}°C every second'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error enabling test mode: {str(e)}'
        })

@app.route('/api/thermal/test_mode/disable', methods=['POST'])
def disable_thermal_test_mode():
    """Disable thermal test mode"""
    if not thermal_camera or not thermal_camera.available:
        return jsonify({
            'success': False,
            'error': 'Thermal camera not available'
        })
    
    try:
        thermal_camera.disable_test_mode()
        
        return jsonify({
            'success': True,
            'message': 'Test mode disabled'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error disabling test mode: {str(e)}'
        })

@app.route('/api/thermal/test_mode/status')
def get_thermal_test_mode_status():
    """Get thermal test mode status"""
    if not thermal_camera or not thermal_camera.available:
        return jsonify({
            'success': False,
            'error': 'Thermal camera not available'
        })
    
    try:
        return jsonify({
            'success': True,
            'test_mode_enabled': thermal_camera.test_mode_enabled,
            'test_temperature': thermal_camera.test_temperature
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting test mode status: {str(e)}'
        })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    
    os.makedirs(templates_dir, exist_ok=True)
    os.makedirs(static_dir, exist_ok=True)
    
    # Run the web server
    app.run(host='0.0.0.0', port=5000, debug=True)

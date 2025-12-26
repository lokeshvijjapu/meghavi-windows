# Meghavi Windows Kiosk System

An intelligent digital signage and kiosk management system designed for interactive displays. This system combines face detection, automated video playback, browser extensions, and WiFi management to create a seamless user experience for public displays.

## 🎯 Overview

This project provides a comprehensive solution for managing interactive kiosk displays with the following capabilities:

- **Smart Screensaver System**: Automatically activates video playback when no face is detected in front of the display
- **Face Detection**: Uses YOLO machine learning model to detect human presence and distance
- **URL-Based Triggering**: Chrome extension integration that activates screensaver based on specific URLs
- **Video Management**: Automatic video download and playlist management from remote API
- **Kiosk Mode Enhancements**: Multiple browser extensions to secure and control the browsing experience
- **WiFi Management**: Built-in WiFi connection management with on-screen keyboard interface

## ✨ Key Features

### 🤖 Intelligent Screensaver
- **Face Detection**: YOLO-based face detection with distance calculation (180cm threshold)
- **Auto-Activation**: Activates after 5 seconds of no face detection
- **Cooldown Period**: 10-second cooldown after manual stop to prevent rapid restart
- **Video Playlist**: Loops through all videos in the `videos` folder
- **Interactive Button**: "Book Your Service Here" overlay button for user interaction
- **Fullscreen Mode**: VLC-based video playback in fullscreen with topmost window

### 🌐 Chrome Extension Integration
- **URL Monitoring**: Monitors active tab URL and triggers screensaver on target page
- **Status Communication**: Real-time communication with Flask server via REST API
- **Seamless Integration**: Automatic screensaver launch/stop based on page navigation

### 🔒 Kiosk Security Extensions
Multiple browser extensions to enhance kiosk mode security:
- **Disable Right-Click**: Prevents context menu access
- **Disable Scroll**: Blocks all scrolling (mouse, keyboard, touch)
- **Disable Swipe Navigation**: Prevents touch swipe gestures
- **Disable Long Press**: Blocks touch-and-hold gestures
- **No Gesture Extension**: Blocks various gesture-based interactions

### 📡 Online Status & WiFi Management
- **Status Indicator**: Visual online/offline status indicator (top-right corner)
- **WiFi Settings**: Modal interface for WiFi connection management
- **On-Screen Keyboard**: QWERTY keyboard with symbol support for credential entry
- **Auto-Connect**: Automatically configures WiFi with highest priority

### 🎬 Video Management Server
- **API Integration**: Downloads videos from remote API endpoint
- **Automatic Updates**: Scheduled or triggered video updates
- **Preview Interface**: Web-based video preview at `http://localhost:5000`
- **Process Management**: Handles screensaver process lifecycle

## 📁 Project Structure

```
meghavi-windows/
├── project/
│   ├── Extensions/                  # Chrome browser extensions
│   │   ├── meghavi-extension/       # Main URL monitoring extension
│   │   ├── disable-right-click/     # Context menu blocker
│   │   ├── disable-scroll-extension/# Scroll prevention
│   │   ├── disable-swipe-navigation/# Touch swipe blocker
│   │   ├── disable-longpress/       # Long press blocker
│   │   ├── no-gesture-extension/    # Gesture blocker
│   │   └── online-status-indicator/ # Connection status & WiFi manager
│   └── python files/
│       ├── screensaver.py           # Main screensaver with face detection
│       ├── server.py                # Flask server for video management
│       ├── wifi_server.py           # WiFi connection management server
│       ├── models/
│       │   └── model.pt            # YOLO face detection model
│       └── videos/                  # Video playlist directory
├── Scripts/                         # Launch scripts
│   ├── open_chrome.bat             # Chrome kiosk mode launcher
│   ├── run_server.bat              # Flask server launcher
│   ├── wifi_server.bat             # WiFi server launcher
│   └── *.vbs                       # Silent background execution scripts
└── video.mp4                        # Default video file
```

## 🔧 Components

### Screensaver (`screensaver.py`)
The core screensaver system that:
- Uses YOLO model for real-time face detection via webcam
- Calculates face distance using calibrated constants (A=9703.20, B=-0.4911842338691967)
- Manages screensaver activation/deactivation based on presence detection
- Integrates VLC media player for video playback
- Provides Tkinter GUI with interactive booking button

**Key Constants:**
- `FACE_DISTANCE_THRESHOLD`: 180cm (faces closer activate screensaver stop)
- `NO_FACE_TIMER_SECONDS`: 5 seconds before screensaver activation
- `COOLDOWN_SECONDS`: 10 seconds cooldown after manual stop

### Server (`server.py`)
Flask server that provides:
- `/url_matched` endpoint: Receives URL status from Chrome extension
- `/trigger-download` endpoint: Downloads and updates video playlist
- `/` route: Video preview web interface
- Screensaver process management (start/stop)
- Video download from `http://api.meghaviwellness.co.in/api/videos/download-all`

### WiFi Server (`wifi_server.py`)
Flask server (port 5050) for WiFi management:
- `/connect` endpoint: Creates Windows WiFi profile and connects
- XML profile generation for WPA2PSK networks
- Auto-connect configuration with highest priority
- Connection logging to `%USERPROFILE%\wifi_connect_log.txt`

### Meghavi Extension
Chrome extension that:
- Monitors active tab URL every 2 seconds
- Detects target URL: `https://outlet.meghaviwellness.co.in/shop/RelaxationTherapy`
- Sends POST requests to `http://127.0.0.1:5000/url_matched` with status (`entered`/`left`)
- Triggers screensaver activation/deactivation based on page navigation

### Online Status Indicator Extension
Provides:
- Visual connection status indicator (green/red dot)
- WiFi settings button (appears when offline)
- Modal interface with on-screen keyboard
- Integration with WiFi server for credential submission

## 🔄 How It Works

### Screensaver Activation Flow

1. **Face Detection Loop**: Continuously monitors webcam for faces
2. **No Face Detected**: After 5 seconds without a face, screensaver activates
3. **Video Playback**: VLC plays videos from `videos/` folder in loop
4. **Face Detected**: When face detected within 180cm, screensaver stops
5. **Manual Stop**: User can click "Book Your Service Here" button to stop

### URL-Based Triggering Flow

1. **Chrome Extension**: Monitors active tab URL every 2 seconds
2. **Target URL Matched**: When on target page, sends `entered` status
3. **Server Receives**: Flask server launches screensaver process
4. **User Navigates Away**: Extension sends `left` status, server stops screensaver

### Video Update Flow

1. **Trigger Request**: POST to `/trigger-download` endpoint
2. **Stop Screensaver**: Creates `stop_vlc.txt` flag file
3. **Download Videos**: Fetches ZIP from API endpoint
4. **Replace Videos**: Extracts new videos to replace old ones
5. **Resume**: Screensaver can be restarted with new videos

## 🎨 Technologies Used

- **Python 3.x**: Core application logic
- **Flask**: Web server framework
- **YOLO (Ultralytics)**: Face detection model
- **OpenCV**: Video capture and image processing
- **VLC**: Video playback engine
- **Tkinter**: GUI framework for screensaver interface
- **Chrome Extensions**: Browser integration and kiosk enhancements
- **Windows APIs**: WiFi profile management via `netsh`

## 📝 Notes

- The system requires VLC to be installed at `C:\Program Files\VideoLAN\VLC`
- Chrome kiosk mode is configured to open a specific wellness outlet page
- All extensions work together to create a secure, controlled browsing environment
- The WiFi server runs on port 5050, main server on port 5000
- Face detection model file (`model.pt`) must be present in `models/` directory

## 🔐 Security Features

- Right-click context menu blocking
- Scroll prevention (mouse, keyboard, touch)
- Gesture blocking (swipe, long-press)
- Touch interaction restrictions
- Kiosk mode with restricted browser features

---

**Built for Meghavi Wellness digital signage and kiosk systems**


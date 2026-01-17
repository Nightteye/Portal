# 🌌 PORTAL (WiFi-Yeet)

**A Sci-Fi themed, lightning-fast local file transfer tool.**

Portal spins up a temporary web server on your local network, generates a QR code, and lets you "beam" files between your PC and phone instantly. No Internet required. No Cloud. No size limits.

![Python](https://img.shields.io/badge/Made%20with-Python-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features
* **0-Dependencies:** Single Python file. No HTML/CSS assets to lose.
* **Bi-Directional:** Send files *to* your phone and *from* your phone.
* **Cyberpunk UI:** Custom CSS animations, drag-and-drop zone, and glassmorphism design.
* **Privacy First:** Runs entirely on local WiFi. Data never leaves your room.

## 🚀 Quick Start

### Prerequisites
* Python 3.x
* A phone and PC on the **same WiFi network**.

### Installation
1.  Clone this repo:
    ```bash
    git clone [https://github.com/Nightteye/portal.git](https://github.com/Nightteye/portal.git)
    cd portal
    ```
2.  Install the QR library:
    ```bash
    pip install -r requirements.txt
    ```

### Usage
Run the script:
```bash
python portal.py
```

### How it Works

1. A QR code will appear in your terminal.

2. Scan it with your phone.

3. Yeet files back and forth!

4. Backend: Python http.server handles GET/POST requests.

5. Frontend: HTML/CSS is injected directly from the Python script to the browser.

6. Network: Automatically detects your local IP to generate the connection link.


### Note

This tool is designed for local trusted networks (Home/Office). Do not run this on public WiFi (Airports/Cafes) as anyone on the network could potentially access your file list.



Built with code and caffeine.
# 🥌 WINCURL 3.0

WinCurl 3.0 is a Python-based curling simulation built with Pygame. It offers a physics-driven curling experience with local and multiplayer capabilities.

## 📋 Overview

"WinCurl" is a modern curling game featuring realistic physics, network matchmaking, and a clean, responsive UI with procedural graphics and 2D pixel art cutscenes.

## 🚀 Features

- 🎯 **Realistic Physics**: Precision curling stone mechanics with accurate friction and curl.
- 🌐 **Global Multiplayer**: Built-in network matchmaking for online competitive play.
- 🎨 **Modern Visuals**: A responsive UI featuring glassmorphism, procedural graphics, and 2D pixel art.
- 🎶 **Procedural Phonk Audio**: An insanely fast, non-blocking audio engine that bumps custom synthesized beats while keeping the gameplay buttery smooth!
- 📱 **Cross-Platform**: Playable on desktop and Android devices.

## 🛠 Technology Stack

- **Language**: Python 3
- **Graphics**: Pygame
- **Build System**: Buildozer / Android SDK

## 📦 Getting Started

1. **Clone the repository**:
   ```bash
   git clone <repo_url>
   ```

2. **Install dependencies**:
   ```bash
   pip install pygame
   ```

3. **Run the game**:
   ```bash
   python main.py
   ```

### 🎮 Steam Controller Support

WinCurl has **native support** for both the original Steam Controller and the new 2026 IBEX models!

It uses the [steamcontroller-haptics](https://pypi.org/project/steamcontroller-haptics/) library to provide incredibly low-latency haptic feedback, including cursor clicks, UI hover effects, and physics-based collision rumbles, while allowing the controller to remain in standard OS Lizard Mode.

**Linux / Arch Linux users:**
You no longer need `python-libusb1`. Simply ensure you have the `steamcontroller-haptics` library installed:
```bash
pip install steamcontroller-haptics
```
*Note: Make sure your `udev` rules are configured to grant `/dev/hidraw` access, as detailed in the package documentation!*

## 📱 Android Deployment

This project is configured for Android deployment. 
- **Download**: You can download `wincurl_latest.apk` directly from the repository releases and sideload it.
- **Features**: Includes full color native emoji support, latency optimizations, clipboard pasting integration, and automatic background pausing during incoming calls to prevent crashes.
- **Developers**: The repository includes automated GitHub Actions that build the APK natively in the cloud.

## 🤝 Contributing

Contributions are welcome. Feel free to open an issue or submit a pull request if you'd like to help improve the game.

---

*WinCurl 3.0 is a spiritual successor and derives inspiration from the original WinCurl 2.0:*
[View the original on Archive.org](https://archive.org/details/WCURLD)

#!/usr/bin/env bash
# Install Chromium
CHROME_VERSION="121.0.6167.85"  # Pick a stable version
mkdir -p .chromium
cd .chromium
curl -LO "https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/1210655/chrome-linux.zip"
unzip chrome-linux.zip
cd ..

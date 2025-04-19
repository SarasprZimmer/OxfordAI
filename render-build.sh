#!/usr/bin/env bash
# Download Chromium binary for headless Selenium

echo "🔧 Downloading Chromium..."
mkdir -p /tmp/chromium
curl -Lo /tmp/chromium/chrome.zip https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/605673/chrome-linux.zip
unzip /tmp/chromium/chrome.zip -d /opt/render/project/src/chrome-linux


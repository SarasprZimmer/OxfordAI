#!/usr/bin/env bash

echo "🔧 Installing Chromium manually..."

# Download and unzip Chromium
curl -sSL https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/1136583/chrome-linux.zip -o chrome-linux.zip
unzip -q chrome-linux.zip

# Ensure the binary is in the expected location
chmod +x chrome-linux/chrome
echo "✅ Chromium installed!"

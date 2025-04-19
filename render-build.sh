#!/usr/bin/env bash

echo "🔧 Downloading Chromium..."

mkdir -p /opt/render/project/src/chrome-linux
curl -Lo /tmp/chrome.zip https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/605673/chrome-linux.zip
unzip /tmp/chrome.zip -d /opt/render/project/src/chrome-linux


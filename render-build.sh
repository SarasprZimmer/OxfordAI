#!/usr/bin/env bash

# Install dependencies
pip install -r requirements.txt

# Download and extract Chromium
wget https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/1210785/chrome-linux.zip -O /tmp/chromium.zip
unzip /tmp/chromium.zip -d /tmp/
mv /tmp/chrome-linux /opt/render/project/src/chrome-linux

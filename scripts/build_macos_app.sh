#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

PYTHON=${PYTHON:-python3}

"$PYTHON" -m PyInstaller --noconfirm --clean packaging/macos/VoiceWeather.spec
codesign --verify --deep --strict "dist/Voice Weather.app"
ditto -c -k --sequesterRsrc --keepParent "dist/Voice Weather.app" "dist/Voice-Weather-macOS.zip"

echo "Built dist/Voice Weather.app"
echo "Built dist/Voice-Weather-macOS.zip"

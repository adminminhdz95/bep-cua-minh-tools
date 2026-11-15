#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
for tool in python3 ffmpeg ffprobe; do
  command -v "$tool" >/dev/null || { echo "Missing $tool. Install python3, python3-venv, ffmpeg and fonts-noto-core using your OS package manager." >&2; exit 1; }
done
test -f /usr/share/fonts/truetype/noto/NotoSans-Bold.ttf || { echo 'Install fonts-noto-core (Noto Sans Vietnamese).' >&2; exit 1; }
python3 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check --no-cache-dir -r requirements.txt
.venv/bin/python render.py --doctor

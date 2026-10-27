#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
[[ "$(uname -m)" == arm64 ]] || { echo 'Build on an Apple Silicon Mac'; exit 1; }
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --windowed --onedir --name BananaSplit --target-arch arm64 --osx-bundle-identifier com.bananasplit.folderstudio --icon assets/banana.png app.py
printf '\nBuilt: %s/dist/BananaSplit.app\n' "$PWD"

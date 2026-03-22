#!/bin/bash
# ShinPlay — macOS Starter
cd "$(dirname "$0")"
python3 shinplay-gui.py "$@" &
disown

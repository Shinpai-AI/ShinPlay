#!/bin/bash
# 🎵 ShinPlay — Spotify Song Downloader by Shinpai-AI
export PATH="$HOME/.deno/bin:$HOME/.local/bin:$PATH"
cd "$(dirname "$0")"
nohup /usr/bin/python3 shinplay-gui.py "$@" &>/dev/null &
sleep 0.5
exit 0

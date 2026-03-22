#!/bin/bash
# ShinPlay Installer — macOS
echo "================================================"
echo "  ShinPlay v1.0.0 - Spotify Song Downloader"
echo "  by Shinpai-AI"
echo "================================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python3 nicht gefunden!"
    echo "   Installiere: brew install python3"
    exit 1
fi
echo "✅ Python3 $(python3 --version)"

# Install yt-dlp
echo "📦 Installiere yt-dlp..."
pip3 install --user yt-dlp &>/dev/null
echo "✅ yt-dlp"

# Check ffmpeg
if ! command -v ffmpeg &>/dev/null; then
    echo "📦 Installiere ffmpeg..."
    brew install ffmpeg &>/dev/null || echo "⚠️ brew nicht gefunden — bitte ffmpeg manuell installieren"
fi
echo "✅ ffmpeg"

echo ""
echo "================================================"
echo "  ✅ Installation abgeschlossen!"
echo "  Starte mit: python3 shinplay-gui.py"
echo "  Oder doppelklick auf start.command"
echo "================================================"

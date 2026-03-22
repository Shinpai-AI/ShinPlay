@echo off
title ShinPlay Installer
echo ================================================
echo   ShinPlay v1.0.0 - Spotify Song Downloader
echo   by Shinpai-AI
echo ================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python nicht gefunden!
    echo Bitte installiere Python von https://python.org
    echo WICHTIG: "Add Python to PATH" anhaken!
    pause
    exit /b 1
)
echo [OK] Python gefunden

:: Install yt-dlp
echo [..] Installiere yt-dlp...
pip install --user yt-dlp >nul 2>&1
echo [OK] yt-dlp

:: Install winsdk (fuer Medienerkennung)
echo [..] Installiere winsdk...
pip install --user winsdk >nul 2>&1
echo [OK] winsdk

:: Check ffmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [WARNUNG] ffmpeg nicht gefunden!
    echo Bitte installiere ffmpeg:
    echo   1. https://ffmpeg.org/download.html
    echo   2. Entpacken nach C:\ffmpeg
    echo   3. C:\ffmpeg\bin zu PATH hinzufuegen
    echo.
)

echo.
echo ================================================
echo   Installation abgeschlossen!
echo   Starte ShinPlay mit: python shinplay-gui.py
echo   Oder doppelklick auf start.bat
echo ================================================
echo.
pause

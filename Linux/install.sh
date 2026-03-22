#!/bin/bash
# ╔══════════════════════════════════════════════╗
# ║  🎵 ShinPlay Installer                      ║
# ║  Spotify Song Downloader by Shinpai-AI       ║
# ║  Unterstützt: Debian/Ubuntu, Fedora/Nobara,  ║
# ║  Arch/Manjaro, openSUSE                      ║
# ╚══════════════════════════════════════════════╝

set -e

APP_NAME="ShinPlay"
APP_VERSION="1.0.0"
DEFAULT_INSTALL_DIR="$HOME/.local/share/shinplay"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/512x512/apps"
BIN_DIR="$HOME/.local/bin"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}"
echo "╔══════════════════════════════════════════════╗"
echo "║  🎵 ShinPlay Installer v${APP_VERSION}               ║"
echo "║  Spotify Song Downloader by Shinpai-AI       ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# === DISTRO ERKENNUNG ===
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO_ID="$ID"
        DISTRO_LIKE="$ID_LIKE"
        DISTRO_NAME="$PRETTY_NAME"
    else
        DISTRO_ID="unknown"
        DISTRO_LIKE=""
        DISTRO_NAME="Unknown"
    fi

    # Paketmanager bestimmen
    if command -v dnf &>/dev/null; then
        PKG_MANAGER="dnf"
        PKG_INSTALL="sudo dnf install -y"
    elif command -v apt &>/dev/null; then
        PKG_MANAGER="apt"
        PKG_INSTALL="sudo apt install -y"
    elif command -v pacman &>/dev/null; then
        PKG_MANAGER="pacman"
        PKG_INSTALL="sudo pacman -S --noconfirm"
    elif command -v zypper &>/dev/null; then
        PKG_MANAGER="zypper"
        PKG_INSTALL="sudo zypper install -y"
    else
        PKG_MANAGER="unknown"
        PKG_INSTALL=""
    fi

    echo -e "  System: ${GREEN}${DISTRO_NAME}${NC}"
    echo -e "  Paketmanager: ${GREEN}${PKG_MANAGER}${NC}"
    echo ""
}

# === INSTALLATIONSPFAD WÄHLEN ===
choose_install_dir() {
    echo -e "${YELLOW}📁 Wohin installieren?${NC}"
    echo -e "  Standard: ${GREEN}${DEFAULT_INSTALL_DIR}${NC}"
    read -p "  Pfad [Enter = Standard]: " CUSTOM_DIR

    if [ -n "$CUSTOM_DIR" ]; then
        INSTALL_DIR="$(eval echo "$CUSTOM_DIR")"
    else
        INSTALL_DIR="$DEFAULT_INSTALL_DIR"
    fi

    echo -e "  → Installiere nach: ${GREEN}${INSTALL_DIR}${NC}"
    echo ""
}

# === DEPENDENCIES INSTALLIEREN ===
install_deps() {
    echo -e "${YELLOW}📦 Prüfe Abhängigkeiten...${NC}"

    NEED_INSTALL=""

    # Python3
    if command -v python3 &>/dev/null; then
        echo -e "  ✅ Python3 $(python3 --version 2>&1 | cut -d' ' -f2)"
    else
        echo -e "  ❌ Python3 fehlt!"
        case $PKG_MANAGER in
            dnf) NEED_INSTALL="$NEED_INSTALL python3" ;;
            apt) NEED_INSTALL="$NEED_INSTALL python3" ;;
            pacman) NEED_INSTALL="$NEED_INSTALL python" ;;
            zypper) NEED_INSTALL="$NEED_INSTALL python3" ;;
        esac
    fi

    # tkinter
    if python3 -c "import tkinter" &>/dev/null; then
        echo -e "  ✅ tkinter"
    else
        echo -e "  ❌ tkinter fehlt!"
        case $PKG_MANAGER in
            dnf) NEED_INSTALL="$NEED_INSTALL python3-tkinter" ;;
            apt) NEED_INSTALL="$NEED_INSTALL python3-tk" ;;
            pacman) NEED_INSTALL="$NEED_INSTALL tk" ;;
            zypper) NEED_INSTALL="$NEED_INSTALL python3-tk" ;;
        esac
    fi

    # ffmpeg
    if command -v ffmpeg &>/dev/null; then
        echo -e "  ✅ ffmpeg"
    else
        echo -e "  ❌ ffmpeg fehlt!"
        NEED_INSTALL="$NEED_INSTALL ffmpeg"
    fi

    # playerctl
    if command -v playerctl &>/dev/null; then
        echo -e "  ✅ playerctl"
    else
        echo -e "  ❌ playerctl fehlt!"
        NEED_INSTALL="$NEED_INSTALL playerctl"
    fi

    # yt-dlp (pip)
    if command -v yt-dlp &>/dev/null; then
        echo -e "  ✅ yt-dlp $(yt-dlp --version 2>/dev/null)"
    else
        echo -e "  ❌ yt-dlp fehlt — installiere via pip..."
        python3 -m pip install --user yt-dlp &>/dev/null && echo -e "  ✅ yt-dlp installiert!" || echo -e "  ⚠️  yt-dlp pip install fehlgeschlagen"
    fi

    # deno (für yt-dlp YouTube JS Runtime)
    if command -v deno &>/dev/null || [ -f "$HOME/.deno/bin/deno" ]; then
        echo -e "  ✅ deno"
    else
        echo -e "  ❌ deno fehlt — installiere..."
        curl -fsSL https://deno.land/install.sh | sh &>/dev/null && echo -e "  ✅ deno installiert!" || echo -e "  ⚠️  deno install fehlgeschlagen"
    fi

    # System-Pakete installieren
    if [ -n "$NEED_INSTALL" ]; then
        echo ""
        echo -e "  ${YELLOW}Installiere: ${NEED_INSTALL}${NC}"
        if [ "$PKG_MANAGER" = "unknown" ]; then
            echo -e "  ${RED}❌ Kein unterstützter Paketmanager gefunden!${NC}"
            echo -e "  Bitte manuell installieren: $NEED_INSTALL"
            exit 1
        fi
        $PKG_INSTALL $NEED_INSTALL || {
            echo -e "  ${RED}❌ Installation fehlgeschlagen! Sudo-Passwort nötig?${NC}"
            exit 1
        }
        echo -e "  ${GREEN}✅ System-Pakete installiert!${NC}"
    fi

    echo ""
}

# === APP INSTALLIEREN ===
install_app() {
    echo -e "${YELLOW}🔧 Installiere ShinPlay...${NC}"

    # Installationsordner erstellen
    mkdir -p "$INSTALL_DIR/assets"

    # Dateien kopieren
    cp "$SCRIPT_DIR/shinplay.py" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/shinplay-gui.py" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/assets/icon.png" "$INSTALL_DIR/assets/"
    cp "$SCRIPT_DIR/assets/icon.ico" "$INSTALL_DIR/assets/" 2>/dev/null || true
    chmod +x "$INSTALL_DIR/shinplay.py" "$INSTALL_DIR/shinplay-gui.py"

    echo -e "  ✅ App-Dateien kopiert nach: ${GREEN}${INSTALL_DIR}${NC}"

    # Launcher Script in ~/.local/bin
    mkdir -p "$BIN_DIR"
    cat > "$BIN_DIR/shinplay" << LAUNCHER
#!/bin/bash
export PATH="\$HOME/.deno/bin:\$HOME/.local/bin:\$PATH"
nohup /usr/bin/python3 "$INSTALL_DIR/shinplay-gui.py" "\$@" &>/dev/null &
LAUNCHER
    chmod +x "$BIN_DIR/shinplay"
    echo -e "  ✅ Launcher: ${GREEN}${BIN_DIR}/shinplay${NC}"

    # Desktop Entry
    mkdir -p "$DESKTOP_DIR"
    cat > "$DESKTOP_DIR/shinplay.desktop" << DESKTOP
[Desktop Entry]
Name=ShinPlay
GenericName=Spotify Song Downloader
Comment=Lädt automatisch Songs die bei Spotify laufen — by Shinpai-AI
Exec=/usr/bin/python3 ${INSTALL_DIR}/shinplay-gui.py
Icon=${INSTALL_DIR}/assets/icon.png
Terminal=false
Type=Application
Categories=AudioVideo;Music;Audio;
Keywords=spotify;download;music;mp3;shinplay;shinpai;
StartupNotify=false
DESKTOP
    chmod +x "$DESKTOP_DIR/shinplay.desktop"
    echo -e "  ✅ Desktop-Eintrag erstellt"

    # Icon in System-Icons
    mkdir -p "$ICON_DIR"
    cp "$INSTALL_DIR/assets/icon.png" "$ICON_DIR/shinplay.png" 2>/dev/null || true
    echo -e "  ✅ System-Icon installiert"

    # Desktop DB aktualisieren
    update-desktop-database "$DESKTOP_DIR" &>/dev/null || true
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" &>/dev/null || true

    echo ""
}

# === DEINSTALLATION ===
uninstall_app() {
    echo -e "${YELLOW}🗑️  Deinstalliere ShinPlay...${NC}"
    rm -rf "$DEFAULT_INSTALL_DIR"
    rm -f "$BIN_DIR/shinplay"
    rm -f "$DESKTOP_DIR/shinplay.desktop"
    rm -f "$ICON_DIR/shinplay.png"
    update-desktop-database "$DESKTOP_DIR" &>/dev/null || true
    echo -e "  ${GREEN}✅ ShinPlay deinstalliert!${NC}"
    exit 0
}

# === FERTIG ===
finish() {
    echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ ShinPlay erfolgreich installiert!        ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  📍 Installiert in: ${PURPLE}${INSTALL_DIR}${NC}"
    echo -e "  🖥️  Startmenü:     ${PURPLE}ShinPlay${NC} (suchen!)"
    echo -e "  💻 Terminal:       ${PURPLE}shinplay${NC}"
    echo ""
    echo -e "  ${YELLOW}So geht's:${NC}"
    echo -e "  1. Spotify (oder anderen Player) starten"
    echo -e "  2. ShinPlay starten (Startmenü oder 'shinplay')"
    echo -e "  3. Speicherort wählen"
    echo -e "  4. START drücken"
    echo -e "  5. Musik genießen — Songs werden automatisch geladen!"
    echo ""
    echo -e "  🗑️  Deinstallieren: ${PURPLE}bash ${SCRIPT_DIR}/install.sh --uninstall${NC}"
    echo ""
    echo -e "  ${PURPLE}shinpai.de | AGPL-3.0${NC}"
    echo ""

    # Direkt starten?
    read -p "  🎵 ShinPlay jetzt starten? [J/n]: " START_NOW
    if [ "$START_NOW" != "n" ] && [ "$START_NOW" != "N" ]; then
        echo -e "  🚀 Starte ShinPlay..."
        export PATH="$HOME/.deno/bin:$HOME/.local/bin:$PATH"
        nohup /usr/bin/python3 "$INSTALL_DIR/shinplay-gui.py" &>/dev/null &
    fi
}

# === MAIN ===
if [ "$1" = "--uninstall" ]; then
    uninstall_app
fi

detect_distro
choose_install_dir
install_deps
install_app
finish

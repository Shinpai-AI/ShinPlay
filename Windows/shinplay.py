#!/usr/bin/env python3
"""
🎵 ShinPlay — Spotify Song Downloader by Shinpai-AI
Erkennt was bei Spotify läuft, lädt es runter, sortiert es sauber.
Cross-Platform: Linux + Windows (geplant)

Struktur: Zielordner/Künstler/Album/Song.mp3
"""

import subprocess
import os
import sys
import time
import signal
import re
import platform
import shutil
from pathlib import Path

# === CONFIG ===
APP_NAME = "ShinPlay"
APP_VERSION = "1.0.0"
IS_LINUX = platform.system() == "Linux"
IS_WINDOWS = platform.system() == "Windows"
CHECK_INTERVAL = 5
DOWNLOADED = set()

# Deno Path für yt-dlp JS Runtime (Linux)
if IS_LINUX:
    os.environ["PATH"] = os.path.expanduser("~/.deno/bin") + ":" + os.path.expanduser("~/.local/bin") + ":" + os.environ.get("PATH", "")


def sanitize(name):
    """Entfernt ungültige Dateisystem-Zeichen."""
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip('. ')


def check_dependencies():
    """Prüft ob alle benötigten Tools installiert sind."""
    missing = []

    # yt-dlp
    if not shutil.which("yt-dlp"):
        missing.append("yt-dlp")

    # ffmpeg
    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg")

    # playerctl (Linux only)
    if IS_LINUX and not shutil.which("playerctl"):
        missing.append("playerctl")

    return missing


def install_dependencies():
    """Versucht fehlende Dependencies automatisch zu installieren."""
    missing = check_dependencies()
    if not missing:
        return True

    print(f"\n⚠️  Fehlende Abhängigkeiten: {', '.join(missing)}")
    print("📦 Versuche automatische Installation...\n")

    for dep in missing:
        if dep == "yt-dlp":
            print(f"   ⬇️  Installiere {dep}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user", "yt-dlp"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"   ✅ {dep} installiert!")
            else:
                print(f"   ❌ {dep} konnte nicht installiert werden!")
                print(f"      Manuell: pip install yt-dlp")
                return False

        elif dep == "ffmpeg":
            if IS_LINUX:
                print(f"   ⬇️  Installiere {dep}...")
                # Versuche verschiedene Paketmanager
                for cmd in [
                    ["sudo", "-S", "dnf", "install", "-y", "ffmpeg"],
                    ["sudo", "-S", "apt", "install", "-y", "ffmpeg"],
                    ["sudo", "-S", "pacman", "-S", "--noconfirm", "ffmpeg"],
                ]:
                    result = subprocess.run(cmd, capture_output=True, text=True, input="\n")
                    if result.returncode == 0:
                        print(f"   ✅ {dep} installiert!")
                        break
                else:
                    print(f"   ❌ {dep} konnte nicht installiert werden!")
                    print(f"      Manuell: sudo apt install ffmpeg / sudo dnf install ffmpeg")
                    return False
            else:
                print(f"   ❌ {dep} muss manuell installiert werden!")
                print(f"      Download: https://ffmpeg.org/download.html")
                return False

        elif dep == "playerctl":
            print(f"   ⬇️  Installiere {dep}...")
            for cmd in [
                ["sudo", "-S", "dnf", "install", "-y", "playerctl"],
                ["sudo", "-S", "apt", "install", "-y", "playerctl"],
                ["sudo", "-S", "pacman", "-S", "--noconfirm", "playerctl"],
            ]:
                result = subprocess.run(cmd, capture_output=True, text=True, input="\n")
                if result.returncode == 0:
                    print(f"   ✅ {dep} installiert!")
                    break
            else:
                print(f"   ❌ {dep} konnte nicht installiert werden!")
                return False

    # Deno für yt-dlp (Linux)
    if IS_LINUX and not shutil.which("deno"):
        print("   ⬇️  Installiere deno (für yt-dlp YouTube-Support)...")
        result = subprocess.run(
            ["bash", "-c", "curl -fsSL https://deno.land/install.sh | sh"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            os.environ["PATH"] = os.path.expanduser("~/.deno/bin") + ":" + os.environ.get("PATH", "")
            print("   ✅ deno installiert!")

    # Recheck
    still_missing = check_dependencies()
    if still_missing:
        print(f"\n❌ Immer noch fehlend: {', '.join(still_missing)}")
        return False

    print("\n✅ Alle Abhängigkeiten installiert!\n")
    return True


def get_spotify_info():
    """Liest aktuellen Spotify-Song."""
    if IS_LINUX:
        return _get_spotify_linux()
    elif IS_WINDOWS:
        return _get_spotify_windows()
    return None


def _get_spotify_linux():
    """Song-Info via playerctl — erkennt JEDEN MPRIS-kompatiblen Player!
    Spotify, VLC, Firefox/Chrome (YouTube), Rhythmbox, Audacious, etc."""
    try:
        # Finde aktiven Player (der gerade spielt)
        players = subprocess.run(
            ["playerctl", "-l"],
            capture_output=True, text=True, timeout=5
        )
        if not players.stdout.strip():
            return None

        # Prüfe jeden Player ob er spielt
        active_player = None
        for player in players.stdout.strip().split('\n'):
            player = player.strip()
            if not player:
                continue
            status = subprocess.run(
                ["playerctl", "-p", player, "status"],
                capture_output=True, text=True, timeout=5
            )
            if status.stdout.strip() == "Playing":
                active_player = player
                break

        if not active_player:
            return None

        fields = {"player": active_player}
        for key, meta_key in [("title", "xesam:title"), ("artist", "xesam:artist"),
                               ("album", "xesam:album"), ("url", "xesam:url")]:
            result = subprocess.run(
                ["playerctl", "-p", active_player, "metadata", meta_key],
                capture_output=True, text=True, timeout=5
            )
            fields[key] = result.stdout.strip()

        if not fields.get("title") or not fields.get("artist"):
            return None
        return fields
    except Exception:
        return None


def _get_spotify_windows():
    """Spotify-Info via Window Title (Windows)."""
    try:
        import ctypes
        from ctypes import wintypes

        # EnumWindows approach
        EnumWindows = ctypes.windll.user32.EnumWindows
        GetWindowTextW = ctypes.windll.user32.GetWindowTextW
        GetWindowTextLengthW = ctypes.windll.user32.GetWindowTextLengthW

        titles = []

        def callback(hwnd, _):
            length = GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(hwnd, buf, length + 1)
                if " - " in buf.value and buf.value != "Spotify":
                    titles.append(buf.value)
            return True

        EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(callback), 0)

        for title in titles:
            # Spotify window format: "Artist - Song Title"
            if " - " in title:
                parts = title.split(" - ", 1)
                return {
                    "artist": parts[0].strip(),
                    "title": parts[1].strip(),
                    "album": "Unknown",
                    "url": ""
                }
    except Exception:
        pass
    return None


def download_song(info, output_dir):
    """Lädt den Song via yt-dlp runter."""
    artist = sanitize(info["artist"])
    album = sanitize(info.get("album", "Unknown"))
    title = sanitize(info["title"])

    song_dir = Path(output_dir) / artist / album
    song_dir.mkdir(parents=True, exist_ok=True)

    song_file = song_dir / f"{title}.mp3"

    if song_file.exists():
        return "EXISTS", str(song_file)

    search = f"{info['artist']} - {info['title']}"
    try:
        cmd = [
            "yt-dlp",
            f"ytsearch1:{search}",
            "-x", "--audio-format", "mp3",
            "--audio-quality", "0",
            "-o", str(song_file.with_suffix('.%(ext)s')),
            "--add-metadata",
            "--no-playlist",
        ]

        # Linux: remote-components für bessere YouTube-Kompatibilität
        if IS_LINUX:
            cmd.insert(3, "--remote-components")
            cmd.insert(4, "ejs:github")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            return "OK", str(song_file)
        else:
            return f"ERROR: {result.stderr[:200]}", None
    except subprocess.TimeoutExpired:
        return "ERROR: Timeout (120s)", None
    except Exception as e:
        return f"ERROR: {e}", None


def create_desktop_entry():
    """Erstellt einen Desktop-Eintrag (Linux) für die App."""
    if not IS_LINUX:
        return

    script_dir = Path(__file__).parent.resolve()
    icon_path = script_dir / "assets" / "icon.png"
    desktop_entry = f"""[Desktop Entry]
Name=ShinPlay
Comment=Spotify Song Downloader by Shinpai-AI
Exec=bash -c 'cd "{script_dir}" && python3 "{script_dir}/shinplay.py"'
Icon={icon_path}
Terminal=true
Type=Application
Categories=AudioVideo;Music;
Keywords=spotify;download;music;
"""
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = desktop_dir / "shinplay.desktop"
    desktop_file.write_text(desktop_entry)
    desktop_file.chmod(0o755)
    print(f"🖥️  Desktop-Eintrag erstellt: {desktop_file}")


def print_banner():
    print(f"""
╔══════════════════════════════════════════════╗
║  🎵 ShinPlay v{APP_VERSION}                          ║
║  Spotify Song Downloader by Shinpai-AI       ║
║                                              ║
║  ▶  Spotify starten und Musik spielen        ║
║  ⏹  Ctrl+C zum Stoppen                      ║
║                                              ║
║  Songs werden automatisch erkannt,           ║
║  heruntergeladen und sortiert!               ║
║  Struktur: Künstler/Album/Song.mp3           ║
╚══════════════════════════════════════════════╝
    System: {platform.system()} | Python {platform.python_version()}
""")


def first_run_setup():
    """Erster Start — Dependencies installieren, Desktop-Entry erstellen."""
    setup_marker = Path(__file__).parent / ".shinplay_setup_done"

    if setup_marker.exists():
        # Quick dependency check
        missing = check_dependencies()
        if missing:
            print(f"⚠️  Fehlende Abhängigkeiten: {', '.join(missing)}")
            if not install_dependencies():
                sys.exit(1)
        return

    print("🎉 Willkommen bei ShinPlay! Erster Start — Setup läuft...\n")

    if not install_dependencies():
        print("\n❌ Setup fehlgeschlagen. Bitte installiere die Abhängigkeiten manuell.")
        sys.exit(1)

    if IS_LINUX:
        create_desktop_entry()

    setup_marker.touch()
    print("\n✅ Setup abgeschlossen! ShinPlay ist bereit!\n")


def main():
    print_banner()
    first_run_setup()

    # Zielordner
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    else:
        if IS_LINUX:
            default = str(Path.home() / "Musik" / "ShinPlay")
        else:
            default = str(Path.home() / "Music" / "ShinPlay")

        user_input = input(f"📁 Speicherort [{default}]: ").strip()
        output_dir = user_input if user_input else default

    output_dir = os.path.expanduser(output_dir)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(f"\n✅ Speichere nach: {output_dir}")
    print(f"⏳ Warte auf Spotify...\n")

    running = [True]
    song_count = [0]

    def stop(sig, frame):
        running[0] = False
        print(f"\n\n⏹  Gestoppt! {song_count[0]} Songs geladen.")
        print(f"📁 Gespeichert in: {output_dir}")
        sys.exit(0)

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    last_song = None

    while running[0]:
        info = get_spotify_info()

        if info:
            song_id = f"{info['artist']} - {info['title']}"

            if song_id != last_song and song_id not in DOWNLOADED:
                last_song = song_id
                album = info.get('album', '?')

                # Check ob schon als Datei vorhanden
                artist = sanitize(info["artist"])
                album_s = sanitize(album)
                title = sanitize(info["title"])
                check_path = Path(output_dir) / artist / album_s / f"{title}.mp3"

                if check_path.exists():
                    print(f"⏭️  {song_id} — bereits vorhanden!")
                    DOWNLOADED.add(song_id)
                else:
                    player_name = info.get('player', '?')
                    print(f"🎵 [{player_name}] {info['artist']} — {info['title']} ({album})")
                    print(f"   ⬇️  Lade...", end=" ", flush=True)

                    result, filepath = download_song(info, output_dir)

                    if result == "EXISTS":
                        print("⏭️  Bereits vorhanden!")
                    elif result == "OK":
                        song_count[0] += 1
                        DOWNLOADED.add(song_id)
                        print(f"✅ Gespeichert! [{song_count[0]}]")
                        print(f"   📂 {artist}/{album_s}/{title}.mp3")
                    else:
                        print(f"❌ {result}")

                    print()
            elif song_id != last_song:
                last_song = song_id

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()

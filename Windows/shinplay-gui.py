#!/usr/bin/env python3
"""
🎵 ShinPlay GUI — Spotify Song Downloader by Shinpai-AI
Elegante GUI, System-Tray Icon, automatischer Download.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import sys
import time
import re
import platform
import shutil
import threading
from pathlib import Path

APP_NAME = "ShinPlay"
APP_VERSION = "1.0.0"
SYSTEM = platform.system()
IS_LINUX = SYSTEM == "Linux"
IS_WINDOWS = SYSTEM == "Windows"
IS_MAC = SYSTEM == "Darwin"

if IS_WINDOWS:
    CONFIG_DIR = Path.home() / "AppData" / "Local" / "ShinPlay"
elif IS_MAC:
    CONFIG_DIR = Path.home() / "Library" / "Application Support" / "ShinPlay"
else:
    CONFIG_DIR = Path.home() / ".config" / "shinplay"
CONFIG_FILE = CONFIG_DIR / "settings.json"


def load_config():
    """Lädt gespeicherte Einstellungen."""
    try:
        if CONFIG_FILE.exists():
            import json
            return json.loads(CONFIG_FILE.read_text())
    except Exception:
        pass
    return {}


def save_config(config):
    """Speichert Einstellungen."""
    try:
        import json
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(config, indent=2))
    except Exception:
        pass

# Deno Path
if IS_LINUX:
    os.environ["PATH"] = os.path.expanduser("~/.deno/bin") + ":" + os.path.expanduser("~/.local/bin") + ":" + os.environ.get("PATH", "")

# === COLORS (Boss-Style) ===
BG_DARK = "#1a1720"
BG_CARD = "#2a2632"
BG_INPUT = "#33303c"
FG_WHITE = "#f0ece4"
FG_GRAY = "#8a8a9a"
FG_PURPLE = "#a832b8"
FG_ORANGE = "#e8724a"
FG_GREEN = "#00b464"
FG_RED = "#c0392b"


def sanitize(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip('. ')


def get_player_info():
    """Liest Song-Info — plattformübergreifend."""
    if IS_LINUX:
        return _get_player_linux()
    elif IS_WINDOWS:
        return _get_player_windows()
    elif IS_MAC:
        return _get_player_mac()
    return None


def _get_player_linux():
    """Linux: playerctl (MPRIS) — erkennt JEDEN Player."""
    try:
        players = subprocess.run(
            ["playerctl", "-l"], capture_output=True, text=True, timeout=5
        )
        if not players.stdout.strip():
            return None
        for player in players.stdout.strip().split('\n'):
            player = player.strip()
            if not player:
                continue
            status = subprocess.run(
                ["playerctl", "-p", player, "status"],
                capture_output=True, text=True, timeout=5
            )
            if status.stdout.strip() == "Playing":
                fields = {"player": player}
                for key, meta_key in [("title", "xesam:title"), ("artist", "xesam:artist"),
                                       ("album", "xesam:album")]:
                    result = subprocess.run(
                        ["playerctl", "-p", player, "metadata", meta_key],
                        capture_output=True, text=True, timeout=5
                    )
                    fields[key] = result.stdout.strip()
                if fields.get("title") and fields.get("artist"):
                    return fields
        return None
    except Exception:
        return None


def _get_player_windows():
    """Windows: Spotify Window-Title + WinRT für andere Player."""
    # Methode 1: WinRT (Windows 10+) — beste Methode
    try:
        from winsdk.windows.media.control import \
            GlobalSystemMediaTransportControlsSessionManager as MediaManager
        import asyncio

        async def get_media_info():
            sessions = await MediaManager.request_async()
            session = sessions.get_current_session()
            if session:
                info = await session.try_get_media_properties_async()
                return {
                    "title": info.title,
                    "artist": info.artist,
                    "album": info.album_title or "Unknown",
                    "player": session.source_app_user_model_id or "Unknown"
                }
            return None

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(get_media_info())
        loop.close()
        if result and result.get("title") and result.get("artist"):
            return result
    except Exception:
        pass

    # Methode 2: Spotify Window Title Fallback
    try:
        import ctypes
        from ctypes import wintypes

        EnumWindows = ctypes.windll.user32.EnumWindows
        GetWindowTextW = ctypes.windll.user32.GetWindowTextW
        GetWindowTextLengthW = ctypes.windll.user32.GetWindowTextLengthW
        GetClassNameW = ctypes.windll.user32.GetClassNameW

        spotify_title = [None]

        def callback(hwnd, _):
            cls = ctypes.create_unicode_buffer(256)
            GetClassNameW(hwnd, cls, 256)
            if "Chrome_WidgetWin" in cls.value or "SpotifyMainWindow" in cls.value:
                length = GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    GetWindowTextW(hwnd, buf, length + 1)
                    if " - " in buf.value and buf.value not in ("Spotify", "Spotify Premium"):
                        spotify_title[0] = buf.value
            return True

        EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(callback), 0)

        if spotify_title[0] and " - " in spotify_title[0]:
            parts = spotify_title[0].split(" - ", 1)
            return {
                "artist": parts[0].strip(),
                "title": parts[1].strip(),
                "album": "Unknown",
                "player": "spotify"
            }
    except Exception:
        pass

    return None


def _get_player_mac():
    """macOS: AppleScript für Spotify + osascript für andere Player."""
    # Spotify
    try:
        script = '''
        tell application "System Events"
            if exists (process "Spotify") then
                tell application "Spotify"
                    if player state is playing then
                        set trackName to name of current track
                        set trackArtist to artist of current track
                        set trackAlbum to album of current track
                        return trackArtist & "|||" & trackName & "|||" & trackAlbum
                    end if
                end tell
            end if
        end tell
        '''
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip() and "|||" in result.stdout:
            parts = result.stdout.strip().split("|||")
            if len(parts) >= 3:
                return {
                    "artist": parts[0],
                    "title": parts[1],
                    "album": parts[2],
                    "player": "spotify"
                }
    except Exception:
        pass

    # Apple Music
    try:
        script = '''
        tell application "System Events"
            if exists (process "Music") then
                tell application "Music"
                    if player state is playing then
                        set trackName to name of current track
                        set trackArtist to artist of current track
                        set trackAlbum to album of current track
                        return trackArtist & "|||" & trackName & "|||" & trackAlbum
                    end if
                end tell
            end if
        end tell
        '''
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip() and "|||" in result.stdout:
            parts = result.stdout.strip().split("|||")
            if len(parts) >= 3:
                return {
                    "artist": parts[0],
                    "title": parts[1],
                    "album": parts[2],
                    "player": "apple-music"
                }
    except Exception:
        pass

    return None


def download_song(info, output_dir):
    """Lädt Song via yt-dlp."""
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
            "yt-dlp", f"ytsearch1:{search}",
            "-x", "--audio-format", "mp3", "--audio-quality", "0",
            "--remote-components", "ejs:github",
            "-o", str(song_file.with_suffix('.%(ext)s')),
            "--add-metadata", "--no-playlist",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return "OK", str(song_file)
        return f"ERROR", None
    except Exception as e:
        return f"ERROR", None


class ShinPlayApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"ShinPlay v{APP_VERSION}")
        self.root.geometry("520x680")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(False, False)

        # Icon setzen
        icon_path = Path(__file__).parent / "assets" / "icon.png"
        if icon_path.exists():
            try:
                icon = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, icon)
                self._icon_ref = icon
            except Exception:
                pass

        self.running = False
        self.song_count = 0
        self.downloaded = set()
        self.last_song = None
        config = load_config()
        if IS_WINDOWS:
            default_music = str(Path.home() / "Music" / "ShinPlay")
        elif IS_MAC:
            default_music = str(Path.home() / "Music" / "ShinPlay")
        else:
            default_music = str(Path.home() / "Musik" / "ShinPlay")
        self.output_dir = config.get("output_dir", default_music)

        self._build_ui()

    def _build_ui(self):
        # === HEADER ===
        header = tk.Frame(self.root, bg=BG_DARK, pady=15)
        header.pack(fill="x")

        # Logo
        icon_path = Path(__file__).parent / "assets" / "icon.png"
        if icon_path.exists():
            try:
                self._logo_img = tk.PhotoImage(file=str(icon_path)).subsample(6, 6)
                tk.Label(header, image=self._logo_img, bg=BG_DARK).pack()
            except Exception:
                pass

        tk.Label(header, text="ShinPlay", font=("Helvetica", 22, "bold"),
                 fg=FG_WHITE, bg=BG_DARK).pack()
        tk.Label(header, text="Spotify Song Downloader by Shinpai-AI",
                 font=("Helvetica", 9), fg=FG_GRAY, bg=BG_DARK).pack()

        # === OUTPUT DIR ===
        dir_frame = tk.Frame(self.root, bg=BG_DARK, padx=20, pady=5)
        dir_frame.pack(fill="x")

        tk.Label(dir_frame, text="📁 SPEICHERORT", font=("Helvetica", 8, "bold"),
                 fg=FG_ORANGE, bg=BG_DARK, anchor="w").pack(fill="x")

        dir_row = tk.Frame(dir_frame, bg=BG_DARK)
        dir_row.pack(fill="x", pady=3)

        self.dir_var = tk.StringVar(value=self.output_dir)
        self.dir_entry = tk.Entry(dir_row, textvariable=self.dir_var,
                                   font=("Helvetica", 10), bg=BG_INPUT, fg=FG_WHITE,
                                   insertbackground=FG_WHITE, relief="flat", bd=8)
        self.dir_entry.pack(side="left", fill="x", expand=True)

        browse_btn = tk.Button(dir_row, text="📂", font=("Helvetica", 12),
                                bg=BG_CARD, fg=FG_WHITE, relief="flat", bd=0,
                                command=self._browse_dir, cursor="hand2",
                                activebackground=FG_PURPLE)
        browse_btn.pack(side="right", padx=(5, 0))

        # === CONTROLS ===
        ctrl_frame = tk.Frame(self.root, bg=BG_DARK, padx=20, pady=10)
        ctrl_frame.pack(fill="x")

        btn_row = tk.Frame(ctrl_frame, bg=BG_DARK)
        btn_row.pack()

        self.start_btn = tk.Button(btn_row, text="▶  START", font=("Helvetica", 13, "bold"),
                                    bg=FG_GREEN, fg=BG_DARK, relief="flat", bd=0,
                                    padx=30, pady=8, cursor="hand2",
                                    command=self._toggle_recording,
                                    activebackground="#00d477")
        self.start_btn.pack(side="left", padx=5)

        # === STATUS ===
        status_frame = tk.Frame(self.root, bg=BG_CARD, padx=20, pady=12)
        status_frame.pack(fill="x", padx=20, pady=(5, 0))

        self.status_label = tk.Label(status_frame, text="⏸️  Bereit — Drücke START",
                                      font=("Helvetica", 11), fg=FG_GRAY, bg=BG_CARD,
                                      anchor="w")
        self.status_label.pack(fill="x")

        self.player_label = tk.Label(status_frame, text="",
                                      font=("Helvetica", 9), fg=FG_PURPLE, bg=BG_CARD,
                                      anchor="w")
        self.player_label.pack(fill="x")

        self.song_label = tk.Label(status_frame, text="",
                                    font=("Helvetica", 10, "bold"), fg=FG_WHITE, bg=BG_CARD,
                                    anchor="w", wraplength=460)
        self.song_label.pack(fill="x", pady=(3, 0))

        self.album_label = tk.Label(status_frame, text="",
                                     font=("Helvetica", 9), fg=FG_GRAY, bg=BG_CARD,
                                     anchor="w")
        self.album_label.pack(fill="x")

        # === COUNTER ===
        counter_frame = tk.Frame(self.root, bg=BG_DARK, pady=10)
        counter_frame.pack(fill="x")

        self.counter_label = tk.Label(counter_frame, text="0",
                                       font=("Helvetica", 36, "bold"), fg=FG_PURPLE, bg=BG_DARK)
        self.counter_label.pack()
        tk.Label(counter_frame, text="SONGS GELADEN",
                 font=("Helvetica", 8, "bold"), fg=FG_GRAY, bg=BG_DARK).pack()

        # === LOG ===
        log_frame = tk.Frame(self.root, bg=BG_DARK, padx=20, pady=5)
        log_frame.pack(fill="both", expand=True)

        tk.Label(log_frame, text="📋 LOG", font=("Helvetica", 8, "bold"),
                 fg=FG_ORANGE, bg=BG_DARK, anchor="w").pack(fill="x")

        self.log_text = tk.Text(log_frame, height=10, font=("Consolas", 9),
                                 bg=BG_INPUT, fg=FG_GRAY, relief="flat", bd=8,
                                 insertbackground=FG_WHITE, wrap="word",
                                 state="disabled")
        self.log_text.pack(fill="both", expand=True, pady=3)

        # Tag colors
        self.log_text.tag_configure("success", foreground=FG_GREEN)
        self.log_text.tag_configure("error", foreground=FG_RED)
        self.log_text.tag_configure("skip", foreground=FG_ORANGE)
        self.log_text.tag_configure("info", foreground=FG_PURPLE)

        # === FOOTER ===
        tk.Label(self.root, text="shinpai.de | AGPL-3.0",
                 font=("Helvetica", 8), fg=FG_GRAY, bg=BG_DARK).pack(pady=(0, 8))

    def _browse_dir(self):
        path = filedialog.askdirectory(title="Speicherort wählen")
        if path:
            self.dir_var.set(path)
            self.output_dir = path

    def _log(self, msg, tag=None):
        self.log_text.configure(state="normal")
        if tag:
            self.log_text.insert("end", msg + "\n", tag)
        else:
            self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _toggle_recording(self):
        if self.running:
            self.running = False
            self.start_btn.configure(text="▶  START", bg=FG_GREEN)
            self.status_label.configure(text="⏸️  Gestoppt", fg=FG_GRAY)
            self._log(f"⏹ Gestoppt. {self.song_count} Songs geladen.", "info")
        else:
            self.running = True
            self.output_dir = self.dir_var.get()
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            save_config({"output_dir": self.output_dir})
            self.start_btn.configure(text="⏹  STOP", bg=FG_RED)
            self.status_label.configure(text="🔴 Aufnahme läuft...", fg=FG_GREEN)
            self._log(f"▶ Gestartet! Speichere nach: {self.output_dir}", "info")
            threading.Thread(target=self._record_loop, daemon=True).start()

    def _record_loop(self):
        while self.running:
            try:
                info = get_player_info()

                if info:
                    song_id = f"{info['artist']} - {info['title']}"

                    # Update UI
                    self.root.after(0, lambda: self.player_label.configure(
                        text=f"🎧 {info.get('player', '?')}"))
                    self.root.after(0, lambda i=info: self.song_label.configure(
                        text=f"{i['artist']} — {i['title']}"))
                    self.root.after(0, lambda i=info: self.album_label.configure(
                        text=f"💿 {i.get('album', '?')}"))

                    if song_id != self.last_song and song_id not in self.downloaded:
                        self.last_song = song_id
                        artist = sanitize(info["artist"])
                        album_s = sanitize(info.get("album", "Unknown"))
                        title = sanitize(info["title"])
                        check_path = Path(self.output_dir) / artist / album_s / f"{title}.mp3"

                        if check_path.exists():
                            self.downloaded.add(song_id)
                            self.root.after(0, lambda s=song_id:
                                self._log(f"⏭️ {s} — bereits vorhanden", "skip"))
                        else:
                            self.root.after(0, lambda: self.status_label.configure(
                                text="⬇️  Lade herunter...", fg=FG_ORANGE))
                            self.root.after(0, lambda s=song_id:
                                self._log(f"⬇️ {s}...", "info"))

                            result, filepath = download_song(info, self.output_dir)

                            if result == "OK":
                                self.song_count += 1
                                self.downloaded.add(song_id)
                                self.root.after(0, lambda: self.counter_label.configure(
                                    text=str(self.song_count)))
                                self.root.after(0, lambda s=song_id:
                                    self._log(f"✅ {s}", "success"))
                                self.root.after(0, lambda: self.status_label.configure(
                                    text="🔴 Aufnahme läuft...", fg=FG_GREEN))
                            elif result == "EXISTS":
                                self.root.after(0, lambda s=song_id:
                                    self._log(f"⏭️ {s} — bereits vorhanden", "skip"))
                                self.root.after(0, lambda: self.status_label.configure(
                                    text="🔴 Aufnahme läuft...", fg=FG_GREEN))
                            else:
                                self.root.after(0, lambda s=song_id:
                                    self._log(f"❌ {s} — Fehler", "error"))
                                self.root.after(0, lambda: self.status_label.configure(
                                    text="🔴 Aufnahme läuft...", fg=FG_GREEN))

                    elif song_id != self.last_song:
                        self.last_song = song_id

                else:
                    self.root.after(0, lambda: self.player_label.configure(text=""))
                    self.root.after(0, lambda: self.song_label.configure(text="Warte auf Player..."))
                    self.root.after(0, lambda: self.album_label.configure(text=""))

            except Exception as e:
                self.root.after(0, lambda e=e: self._log(f"⚠️ {e}", "error"))

            time.sleep(5)

    def run(self):
        self.root.mainloop()


def install_to_system(app_path):
    """Installiert ShinPlay ins System — Startmenü-Icon + Command."""
    if not IS_LINUX:
        return False

    app_path = Path(app_path).resolve()
    install_dir = Path.home() / ".local" / "share" / "shinplay"
    bin_dir = Path.home() / ".local" / "bin"
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    icon_dir = Path.home() / ".local" / "share" / "icons" / "hicolor" / "512x512" / "apps"

    # Ordner erstellen
    install_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    desktop_dir.mkdir(parents=True, exist_ok=True)
    icon_dir.mkdir(parents=True, exist_ok=True)

    # Herausfinden ob wir als AppImage/PyInstaller oder als Script laufen
    is_frozen = getattr(sys, 'frozen', False)

    if is_frozen:
        # PyInstaller/AppImage Binary — die EXE selbst kopieren
        exe_path = Path(sys.executable).resolve()
        dest = install_dir / "ShinPlay"
        shutil.copy2(str(exe_path), str(dest))
        dest.chmod(0o755)
        exec_cmd = str(dest)

        # Assets aus dem Bundle extrahieren
        bundle_dir = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else exe_path.parent
        assets_src = bundle_dir / "assets"
        assets_dst = install_dir / "assets"
        if assets_src.exists():
            if assets_dst.exists():
                shutil.rmtree(str(assets_dst))
            shutil.copytree(str(assets_src), str(assets_dst))
    else:
        # Python-Script Modus
        for f in app_path.parent.iterdir():
            if f.name.startswith('.') or f.name == '__pycache__' or f.name.startswith('.'):
                continue
            if f.is_dir() and f.name not in ('build', 'dist', '__pycache__'):
                dest_sub = install_dir / f.name
                if dest_sub.exists():
                    shutil.rmtree(str(dest_sub))
                shutil.copytree(str(f), str(dest_sub))
            elif f.is_file():
                shutil.copy2(str(f), str(install_dir / f.name))
        exec_cmd = f"/usr/bin/python3 {install_dir}/shinplay-gui.py"

    # Icon kopieren
    icon_src = install_dir / "assets" / "icon.png"
    if not icon_src.exists() and (app_path.parent / "assets" / "icon.png").exists():
        (install_dir / "assets").mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(app_path.parent / "assets" / "icon.png"), str(icon_src))
    if icon_src.exists():
        shutil.copy2(str(icon_src), str(icon_dir / "shinplay.png"))

    # Desktop Entry
    desktop_entry = f"""[Desktop Entry]
Name=ShinPlay
GenericName=Spotify Song Downloader
Comment=Lädt automatisch Songs die bei Spotify laufen — by Shinpai-AI
Exec={exec_cmd}
Icon={icon_dir}/shinplay.png
Terminal=false
Type=Application
Categories=AudioVideo;Music;Audio;
Keywords=spotify;download;music;mp3;shinplay;
StartupNotify=false
"""
    desktop_file = desktop_dir / "shinplay.desktop"
    desktop_file.write_text(desktop_entry)
    desktop_file.chmod(0o755)

    # CLI Launcher
    launcher = bin_dir / "shinplay"
    launcher.write_text(f"""#!/bin/bash
export PATH="$HOME/.deno/bin:$HOME/.local/bin:$PATH"
nohup {exec_cmd} "$@" &>/dev/null &
""")
    launcher.chmod(0o755)

    # Caches aktualisieren
    subprocess.run(["update-desktop-database", str(desktop_dir)],
                   capture_output=True, timeout=5)
    subprocess.run(["gtk-update-icon-cache", "-f", "-t",
                    str(Path.home() / ".local" / "share" / "icons" / "hicolor")],
                   capture_output=True, timeout=5)

    return True


def show_install_dialog():
    """Zeigt den Installations-Dialog beim ersten Start mit Pfadauswahl."""
    dialog = tk.Tk()
    dialog.title("ShinPlay — Installation")
    dialog.geometry("450x320")
    dialog.configure(bg=BG_DARK)
    dialog.resizable(False, False)

    result = {"install": False, "path": str(Path.home() / ".local" / "share" / "shinplay")}

    # Header
    tk.Label(dialog, text="🎵 Willkommen bei ShinPlay!", font=("Helvetica", 16, "bold"),
             fg=FG_WHITE, bg=BG_DARK).pack(pady=(20, 5))
    tk.Label(dialog, text="Möchtest du ShinPlay fest installieren?",
             font=("Helvetica", 10), fg=FG_GRAY, bg=BG_DARK).pack(pady=(0, 15))

    # Pfadauswahl
    path_frame = tk.Frame(dialog, bg=BG_DARK, padx=20)
    path_frame.pack(fill="x")

    tk.Label(path_frame, text="📁 INSTALLATIONSPFAD", font=("Helvetica", 8, "bold"),
             fg=FG_ORANGE, bg=BG_DARK, anchor="w").pack(fill="x")

    path_row = tk.Frame(path_frame, bg=BG_DARK)
    path_row.pack(fill="x", pady=3)

    path_var = tk.StringVar(value=result["path"])
    path_entry = tk.Entry(path_row, textvariable=path_var, font=("Helvetica", 9),
                           bg=BG_INPUT, fg=FG_WHITE, insertbackground=FG_WHITE,
                           relief="flat", bd=8)
    path_entry.pack(side="left", fill="x", expand=True)

    def browse():
        p = filedialog.askdirectory(title="Installationspfad wählen")
        if p:
            path_var.set(p)

    tk.Button(path_row, text="📂", font=("Helvetica", 12), bg=BG_CARD, fg=FG_WHITE,
              relief="flat", bd=0, command=browse, cursor="hand2").pack(side="right", padx=(5, 0))

    # Info
    tk.Label(dialog, text="✅ Erstellt Startmenü-Icon\n✅ 'shinplay' Command im Terminal\n✅ Jederzeit deinstallierbar",
             font=("Helvetica", 9), fg=FG_GRAY, bg=BG_DARK, justify="left").pack(pady=15)

    # Buttons
    btn_frame = tk.Frame(dialog, bg=BG_DARK)
    btn_frame.pack(pady=10)

    def do_install():
        result["install"] = True
        result["path"] = path_var.get()
        dialog.destroy()

    def do_portable():
        result["install"] = False
        dialog.destroy()

    tk.Button(btn_frame, text="✅ INSTALLIEREN", font=("Helvetica", 11, "bold"),
              bg=FG_GREEN, fg=BG_DARK, relief="flat", padx=20, pady=6,
              command=do_install, cursor="hand2").pack(side="left", padx=5)

    tk.Button(btn_frame, text="Portable", font=("Helvetica", 11),
              bg=BG_CARD, fg=FG_GRAY, relief="flat", padx=20, pady=6,
              command=do_portable, cursor="hand2").pack(side="left", padx=5)

    dialog.mainloop()
    return result


if __name__ == "__main__":
    setup_marker = Path.home() / ".config" / "shinplay" / ".installed"

    if not setup_marker.exists():
        # Erster Start — fragen ob installieren
        result = show_install_dialog()

        if result["install"]:
            custom_path = result["path"]
            app_path = Path(__file__).resolve()

            # Direkt installieren mit custom path
            install_dir = Path(custom_path)
            bin_dir = Path.home() / ".local" / "bin"
            desktop_dir = Path.home() / ".local" / "share" / "applications"
            icon_dir = Path.home() / ".local" / "share" / "icons" / "hicolor" / "512x512" / "apps"

            install_dir.mkdir(parents=True, exist_ok=True)
            bin_dir.mkdir(parents=True, exist_ok=True)
            desktop_dir.mkdir(parents=True, exist_ok=True)
            icon_dir.mkdir(parents=True, exist_ok=True)

            is_frozen = getattr(sys, 'frozen', False)
            if is_frozen:
                exe_path = Path(sys.executable).resolve()
                dest = install_dir / "ShinPlay"
                shutil.copy2(str(exe_path), str(dest))
                dest.chmod(0o755)
                exec_cmd = str(dest)
                bundle_dir = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else exe_path.parent
                assets_src = bundle_dir / "assets"
                assets_dst = install_dir / "assets"
                if assets_src.exists():
                    if assets_dst.exists():
                        shutil.rmtree(str(assets_dst))
                    shutil.copytree(str(assets_src), str(assets_dst))
            else:
                for f in app_path.parent.iterdir():
                    if f.name.startswith('.') or f.name in ('build', 'dist', '__pycache__'):
                        continue
                    if f.is_dir():
                        dest_sub = install_dir / f.name
                        if dest_sub.exists():
                            shutil.rmtree(str(dest_sub))
                        shutil.copytree(str(f), str(dest_sub))
                    elif f.is_file():
                        shutil.copy2(str(f), str(install_dir / f.name))
                exec_cmd = f"/usr/bin/python3 {install_dir}/shinplay-gui.py"

            icon_src = install_dir / "assets" / "icon.png"
            if not icon_src.exists() and (app_path.parent / "assets" / "icon.png").exists():
                (install_dir / "assets").mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(app_path.parent / "assets" / "icon.png"), str(icon_src))
            if icon_src.exists():
                shutil.copy2(str(icon_src), str(icon_dir / "shinplay.png"))

            desktop_file = desktop_dir / "shinplay.desktop"
            desktop_file.write_text(f"""[Desktop Entry]
Name=ShinPlay
GenericName=Spotify Song Downloader
Comment=Lädt automatisch Songs die bei Spotify laufen — by Shinpai-AI
Exec={exec_cmd}
Icon={icon_dir}/shinplay.png
Terminal=false
Type=Application
Categories=AudioVideo;Music;Audio;
Keywords=spotify;download;music;mp3;shinplay;
StartupNotify=false
""")
            desktop_file.chmod(0o755)

            launcher = bin_dir / "shinplay"
            launcher.write_text(f"""#!/bin/bash
export PATH="$HOME/.deno/bin:$HOME/.local/bin:$PATH"
nohup {exec_cmd} "$@" &>/dev/null &
""")
            launcher.chmod(0o755)

            subprocess.run(["update-desktop-database", str(desktop_dir)], capture_output=True, timeout=5)
            success = True
            if success:
                setup_marker.parent.mkdir(parents=True, exist_ok=True)
                setup_marker.touch()
                # Pfad merken für Deinstallation
                (setup_marker.parent / "install_path").write_text(str(custom_path))
                root = tk.Tk()
                root.withdraw()
                messagebox.showinfo(
                    "ShinPlay — Installiert!",
                    f"✅ ShinPlay wurde installiert!\n\n"
                    f"📍 Installiert in: {custom_path}\n"
                    f"🖥️ Startmenü: Suche 'ShinPlay'\n"
                    f"💻 Terminal: shinplay\n\n"
                    f"Die App startet jetzt!"
                )
                root.destroy()

    app = ShinPlayApp()
    app.run()

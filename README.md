# 🎵 ShinPlay — Spotify Song Downloader

**Erkennt automatisch was bei Spotify (oder jedem anderen Player) läuft und lädt es herunter.**

Sauber sortiert. Automatisch. Ohne Gefrickel.

```
Künstler/Album/Song.mp3
```

![ShinPlay](Linux/assets/icon.png)

## Features

- 🎧 **Erkennt jeden Player** — Spotify, VLC, Firefox (YouTube), und alle MPRIS-kompatiblen Player
- ⬇️ **Automatischer Download** — Song erkannt → runtergeladen → sortiert
- 📁 **Saubere Struktur** — Künstler/Album/Song.mp3
- 🔄 **Duplikat-Check** — Kein Song wird doppelt geladen
- 🖥️ **Elegante GUI** — Dark Theme, Start/Stop, Live-Log
- 📦 **AppImage** — Eine Datei, doppelklick, fertig
- 🔧 **Installer** — Startmenü-Icon + Terminal-Command
- 🆓 **Open Source** — AGPL-3.0, für immer frei

## Schnellstart

### Option 1: AppImage (Portable)
```bash
chmod +x ShinPlay-x86_64.AppImage
./ShinPlay-x86_64.AppImage
```
Doppelklick → Läuft. Beim ersten Start: "Installieren?" → JA = Startmenü-Icon.

### Option 2: Installer
```bash
cd Linux
bash install.sh
```
Installiert alles: Dependencies, App, Startmenü-Icon, `shinplay` Command.

### Option 3: Direkt starten
```bash
cd Linux
python3 shinplay-gui.py
```

## So geht's

1. **Spotify** (oder anderen Player) starten
2. **ShinPlay** starten
3. **Speicherort** wählen
4. **START** drücken
5. Musik abspielen — Songs werden automatisch geladen!
6. **STOP** oder `Ctrl+C` zum Beenden

## Voraussetzungen

Werden automatisch vom Installer installiert:

- Python 3.8+
- tkinter
- yt-dlp
- ffmpeg
- playerctl (Linux)
- deno (für yt-dlp YouTube-Support)

## Plattformen

| Plattform | Status |
|-----------|--------|
| Linux (alle Distros) | ✅ Fertig |
| Windows | 🔲 Geplant |
| macOS | 🔲 Geplant |

## Struktur

```
ShinPlay/
├── ShinPlay-x86_64.AppImage   ← Portable (eine Datei!)
├── Linux/
│   ├── shinplay-gui.py        ← GUI
│   ├── shinplay.py            ← Terminal-Version
│   ├── install.sh             ← Installer
│   ├── start.sh               ← Starter
│   └── assets/                ← Icons
├── Windows/                   ← (geplant)
├── MacOS/                     ← (geplant)
├── LICENSE                    ← AGPL-3.0
└── README.md
```

## Lizenz

**AGPL-3.0** — Für immer frei. Für immer offen.

## Credits

Entwickelt von [Shinpai-AI](https://shinpai.de) (Hannes Kell)

---

*Made with conviction, not capital.* 🦋

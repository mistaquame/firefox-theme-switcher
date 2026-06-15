# Firefox Theme Switcher

A lightweight cross-platform desktop tool to switch between downloaded Firefox CSS themes (`userChrome.css` / `userContent.css`) with one click. Dark glass morphism UI styled after the [lyrics-extractor](https://github.com/mistaquame/lyricsextractor) project.

## Features

- **One-click apply** — select a theme and apply it to your Firefox profile
- **Automatic backups** — existing `userChrome.css` / `userContent.css` are backed up to `chrome/backups/<timestamp>/` before applying
- **Active theme indicator** — the currently applied theme has a green border and **ACTIVE** badge (detected via SHA-256 file comparison)
- **GitHub source links** — each theme card can display a GitHub URL; click the link to edit it and save directly to a `source` file in the theme folder
- **Profile picker** — first-launch wizard with a tutorial shows how to find your Firefox profile folder (`about:support`)
- **Safe** — sets `toolkit.legacyUserProfileCustomizations.stylesheets = true` via `user.js` only if not already present

## How to run

**Windows** — double-click `run.bat` or run from terminal:

```bat
python app.py
```

**Linux / macOS** — run from terminal:

```sh
bash run.sh
# or
python3 app.py
```

Requires Python 3.10+. No external dependencies — uses only the Python standard library.

On Linux, the app auto-detects your Firefox profile from `~/.mozilla/firefox/` on first run.

## How to add a theme

Download a Firefox CSS theme (e.g. [FoxOne](https://github.com/Firnschnee/FoxOne)) and place the files in the `themes/` folder:

```
firefox-theme-switcher/
  themes/
    FoxOne/
      userChrome.css
      userContent.css
    AnotherTheme/
      userChrome.css
```

Each folder needs at least `userChrome.css`. Optionally add a `source` file containing the GitHub URL — it will be displayed and editable in the app.

## How to use

1. Run the app.
2. If it's the first run, select your Firefox profile folder:
   - Open Firefox → go to `about:support`
   - Under **Application Basics**, find **Profile Folder** → click **Open Folder**
   - Copy the path and paste it into the app (or use **Browse Folder…**)
3. Once a valid profile is saved, the app scans `themes/` and shows each theme as a card.
4. The currently active theme (if any) is shown with a green border and **ACTIVE** badge.
5. Click **Apply Theme** to switch — the old files are backed up automatically.
6. Restart Firefox to see the changes.

## Project structure

```
firefox-theme-switcher/
  app.py              — main GUI (tkinter)
  config_store.py     — JSON-based config persistence
  theme_manager.py    — theme scanning, apply, backup, detection
  run.bat             — Windows launcher
  run.sh              — Linux/macOS launcher
  themes/             — drop theme folders here
    FoxOne/
      userChrome.css
      userContent.css
      source           — optional GitHub URL (editable from app)
```


from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import hashlib
import shutil
import struct


@dataclass(frozen=True)
class FirefoxTheme:
    name: str
    folder: Path
    source_url: str | None
    user_chrome: Path | None
    user_content: Path | None

    @property
    def has_user_chrome(self) -> bool:
        return self.user_chrome is not None

    @property
    def has_user_content(self) -> bool:
        return self.user_content is not None


def _hash_file(path: Path | None) -> str | None:
    """Return SHA-256 hex digest of a file, or None."""
    if path is None or not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            buf = f.read(65536)
            if not buf:
                break
            h.update(buf)
    return h.hexdigest()


def detect_active_theme(
    profile_folder: Path,
    themes: list[FirefoxTheme],
) -> FirefoxTheme | None:
    """Return which theme matches the files currently in chrome/.

    userChrome.css is the primary check — it must match.  userContent.css
    is checked only if the theme has one; a leftover userContent.css in
    chrome/ from a previous dual-file theme does not prevent a match.
    """
    chrome = profile_folder / "chrome"
    if not chrome.exists():
        return None

    installed_chrome = _hash_file(chrome / "userChrome.css")
    installed_content = _hash_file(chrome / "userContent.css")

    for t in themes:
        # userChrome.css must match
        tc = _hash_file(t.user_chrome)
        if tc is None or tc != installed_chrome:
            continue

        # userContent.css is only checked if the theme ships one
        if t.has_user_content:
            if _hash_file(t.user_content) != installed_content:
                continue

        return t
    return None


def scan_themes(theme_root: Path) -> list[FirefoxTheme]:
    themes: list[FirefoxTheme] = []
    if not theme_root.exists():
        return themes

    for folder in sorted(p for p in theme_root.iterdir() if p.is_dir()):
        user_chrome = folder / "userChrome.css"
        user_content = folder / "userContent.css"
        if user_chrome.exists() or user_content.exists():
            # read optional source file (first line)
            source = None
            for src_file in (folder / "source", folder / "source.txt", folder / "github.url"):
                if src_file.exists():
                    line = src_file.read_text(encoding="utf-8", errors="replace").strip()
                    if line:
                        source = line
                    break
            themes.append(
                FirefoxTheme(
                    name=folder.name,
                    folder=folder,
                    source_url=source,
                    user_chrome=user_chrome if user_chrome.exists() else None,
                    user_content=user_content if user_content.exists() else None,
                )
            )
    return themes


def is_firefox_profile(path: Path) -> bool:
    return path.is_dir() and (path / "prefs.js").exists()


def validate_profile(profile_folder: Path) -> None:
    if not is_firefox_profile(profile_folder):
        raise ValueError("Invalid Firefox profile folder — must contain prefs.js.")


def apply_theme(profile_folder: Path, theme: FirefoxTheme) -> Path:
    chrome_dir = profile_folder / "chrome"
    chrome_dir.mkdir(parents=True, exist_ok=True)

    backup_dir = (
        chrome_dir
        / "backups"
        / datetime.now().strftime("%Y%m%d-%H%M%S")
    )
    backup_dir.mkdir(parents=True, exist_ok=True)

    copied = []

    for source in (theme.user_chrome, theme.user_content):
        if source is None:
            continue
        destination = chrome_dir / source.name
        if destination.exists():
            shutil.copy2(destination, backup_dir / destination.name)
        shutil.copy2(source, destination)
        copied.append(source.name)

    return backup_dir


def ensure_custom_stylesheets_enabled(profile_folder: Path) -> None:
    user_js = profile_folder / "user.js"
    pref = (
        'user_pref('
        '"toolkit.legacyUserProfileCustomizations.stylesheets", '
        "true);\n"
    )

    existing = user_js.read_text(encoding="utf-8") if user_js.exists() else ""
    if "toolkit.legacyUserProfileCustomizations.stylesheets" not in existing:
        with user_js.open("a", encoding="utf-8") as f:
            f.write("\n" + pref)

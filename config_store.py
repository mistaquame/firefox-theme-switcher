from pathlib import Path
import json

DEFAULT_CONFIG = {
    "profile_folder": "",
    "theme_folder": "themes",
}


class ConfigStore:
    def __init__(self, path: Path):
        self.path = path
        self.data = DEFAULT_CONFIG.copy()

    def load(self) -> dict:
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as f:
                self.data = {**DEFAULT_CONFIG, **json.load(f)}
        return self.data

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def set_profile_folder(self, value: str):
        self.data["profile_folder"] = value
        self.save()

    def set_theme_folder(self, value: str):
        self.data["theme_folder"] = value
        self.save()

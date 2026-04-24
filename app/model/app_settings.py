"""Application settings model for the desktop UI."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass
class AppSettings:
    """
    Persisted application settings for TTS generation and playback.
    """

    voice: str = "en-US-GuyNeural"
    speaking_rate: str = "medium"
    synthesis_volume: str = "medium"
    emphasis_level: str = "none"
    pitch: str = "default"
    pitch_range: str = "default"
    pause_duration: str = "none"
    pause_position: str = "after"
    playback_volume: int = 80
    auto_clean_text: bool = True
    logging_enabled: bool = True
    azure_key: str = ""
    azure_region: str = ""
    output_dir: str = "data/dynamic/audio"

    @classmethod
    def load(cls, path):
        """
        Load settings from disk, falling back to defaults if unavailable.
        """
        settings_path = Path(path)
        if not settings_path.exists():
            return cls()

        with open(settings_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return cls(**data)

    def save(self, path):
        """
        Save settings to disk.
        """
        settings_path = Path(path)
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_path, "w", encoding="utf-8") as file:
            json.dump(asdict(self), file, indent=2)

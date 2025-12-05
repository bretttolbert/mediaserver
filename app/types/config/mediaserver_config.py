from dataclasses import dataclass, field
from dataclass_wizard import YAMLWizard

from app.types.config.playback_methods_config import PlaybackMethodsConfig


@dataclass
class MediaServerConfig(YAMLWizard):
    version: int = field(default=1)
    files_yaml_path: str = field(default="../mediascan/out/files.yaml")
    debug: bool = field(default=False)
    host: str = field(default="0.0.0.0")
    port: int = field(default=5000)
    playback_methods: PlaybackMethodsConfig = field(
        default_factory=PlaybackMethodsConfig
    )

from dataclasses import dataclass, field
from dataclass_wizard import YAMLWizard

from app.types.config.playback_methods_config import PlaybackMethodsConfig
from app.types.config.flask_config import FlaskConfig


@dataclass
class MediaServerConfig(YAMLWizard):
    version: int = field(default=1)
    files_yaml_path: str = field(default="../mediascan/out/files.yaml")
    covers_path: str = field(default="/data/")
    flask_config: FlaskConfig = field(default_factory=FlaskConfig)
    playback_methods: PlaybackMethodsConfig = field(
        default_factory=PlaybackMethodsConfig
    )

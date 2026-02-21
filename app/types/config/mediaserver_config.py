from dataclasses import dataclass, field
from dataclass_wizard import YAMLWizard

from app.types.config.playback_methods_config import PlaybackMethodsConfig
from app.types.config.flask_config import FlaskConfig


@dataclass
class MediaServerConfig(YAMLWizard):
    version: int = field(default=1)
    mediascan_database_file_path: str = field(default="sqlite:///../mediascan/out/mediascan.db")
    album_covers_path: str = field(default="/data/")
    age_verification: bool = field(default=True)
    limit_bandwidth: bool = field(default=True)
    max_results: int = field(default=50000)
    max_results_album_covers: int = field(default=500)
    flask_config: FlaskConfig = field(default_factory=FlaskConfig)
    playback_methods: PlaybackMethodsConfig = field(default_factory=PlaybackMethodsConfig)

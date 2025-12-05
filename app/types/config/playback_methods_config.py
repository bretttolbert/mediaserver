from dataclasses import dataclass, field
from dataclass_wizard import YAMLWizard

from app.types.config.local_playback_method_config import LocalPlaybackMethodConfig
from app.types.config.youtube_playback_method_config import YouTubePlaybackMethodConfig


@dataclass
class PlaybackMethodsConfig(YAMLWizard):
    local: LocalPlaybackMethodConfig = field(default_factory=LocalPlaybackMethodConfig)
    youtube: YouTubePlaybackMethodConfig = field(
        default_factory=YouTubePlaybackMethodConfig
    )

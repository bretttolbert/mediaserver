from typing import Optional

from dataclasses import dataclass, field
from dataclass_wizard import YAMLWizard

from app.types.config.local_playback_method_config import LocalPlaybackMethodConfig


@dataclass
class FlaskConfig(YAMLWizard):
    host: str = field(default="0.0.0.0")
    port: int = field(default=5000)
    root_path: Optional[str] = field(default=None)
    url_prefix: Optional[str] = field(default=None)
    debug: bool = field(default=False)

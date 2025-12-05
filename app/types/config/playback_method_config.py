from dataclasses import dataclass, field
from dataclass_wizard import YAMLWizard


@dataclass
class PlaybackMethodConfig(YAMLWizard):
    enabled: bool = field(default=True)

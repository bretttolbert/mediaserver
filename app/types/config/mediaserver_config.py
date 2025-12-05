from dataclasses import dataclass, field
from dataclass_wizard import YAMLWizard


@dataclass
class MediaServerConfig(YAMLWizard):
    version: int = field(default=1)
    MEDIASCAN_FILES_PATH: str = field(default="../mediascan/out/files.yaml")
    # !!! Important security note !!!
    # Do not expose more than you need to with the music lib path below,
    # Every file under this path will be exposed by the server!
    # See the /getfile/ route.
    # TODO: Support multiple specific paths e.g. /data/Music and /data/MusicOther
    MUSIC_LIB_PATH_PREFIX: str = field(default="/data/")
    DEBUG: bool = field(default=False)
    HOST: str = field(default="0.0.0.0")

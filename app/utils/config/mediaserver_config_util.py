from typing import TextIO

from app.utils.config.base_config_util import BaseConfigUtil
from app.types.config.mediaserver_config import MediaServerConfig


class MediaServerConfigUtil(BaseConfigUtil[MediaServerConfig]):
    """
    Utility class for loading mediaserver configuration from YAML config file
    """

    yaml_filename = "mediaserver_config.yaml"
    _yaml_resource_path = None

    def __init__(self) -> None:
        super().__init__(self.yaml_filename)

    def _load_config_from_filestream(self, filestream: TextIO) -> MediaServerConfig:
        ret = MediaServerConfig()
        data = MediaServerConfig.from_yaml(filestream)
        if isinstance(data, list):
            ret = data[0]
        else:
            ret = data
        return ret

    def _load_default_config(self) -> MediaServerConfig:
        return MediaServerConfig()

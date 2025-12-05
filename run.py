import sys
from pathlib import Path

from app import create_app
from app.utils.config.mediaserver_config_util import MediaServerConfigUtil

config_filepath = None
if len(sys.argv) > 1:
    config_filepath = Path(sys.argv[1])
config = MediaServerConfigUtil().load_config(config_filepath)
app = create_app(config)

if __name__ == "__main__":
    app.run(debug=config.debug, host=config.host, port=config.port)

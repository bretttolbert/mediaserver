import sys
from pathlib import Path

from app import create_app
from app.utils.config.mediaserver_config_util import MediaServerConfigUtil

config_filepath = None
if len(sys.argv) > 1:
    config_filepath = Path(sys.argv[1])
    print(f"Loading configuration from file {config_filepath}")
else:
    print("Warning: No config file specified, loading default configuration")
config = MediaServerConfigUtil().load_config(config_filepath)
app = create_app(config)
if config_filepath == None:
    app.logger.warning("No config file specified, loaded default configuration")
else:
    app.logger.info(f"Loaded configuration from file {config_filepath}")

if __name__ == "__main__":
    app.run(
        debug=config.flask_config.debug,
        use_debugger=config.flask_config.use_debugger,
        use_reloader=config.flask_config.use_reloader,
        host=config.flask_config.host,
        port=config.flask_config.port,
    )

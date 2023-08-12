import datetime
import json
import logging
import logging.config
import os


class Log:
    def __new__(cls, name="logger"):
        instance = super().__new__(cls)
        instance.__init__()
        return logging.getLogger(name)

    def __init__(self):
        self.setup_logging()

    def setup_logging(
        self,
        default_path: str = "logging.json",
        default_level: int = logging.INFO,
        env_key: str = "LOG_CFG",
    ):
        path = default_path
        value = os.getenv(env_key, None)
        if value:
            path = value
        if os.path.exists(path):
            with open(path) as f:
                config = json.load(f)
            info_filename = config["handlers"]["info_file_handler"]["filename"]
            error_filename = config["handlers"]["error_file_handler"]["filename"]
            config["handlers"]["info_file_handler"][
                "filename"
            ] = self.setup_filename_path(info_filename, "logs")
            config["handlers"]["error_file_handler"][
                "filename"
            ] = self.setup_filename_path(error_filename, "logs")
            logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=default_level)

    def setup_filename_path(self, filename: str, folder: str) -> str:
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        folder = os.path.join(folder, date_str)
        if not os.path.exists(folder):
            os.makedirs(folder)
        return f"{folder}/{filename}"


logger = Log()

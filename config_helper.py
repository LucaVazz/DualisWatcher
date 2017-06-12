import json
import os


class ConfigHelper:
    """
    Handles the saving, formating and loading of the local configuration.
    """
    def __init__(self):
        self._whole_config = {}

    def is_present(self) -> bool:
        return os.path.isfile('config.json')

    def load(self):
        try:
            with open('config.json', 'r') as f:
                config_raw = f.read()
                self._whole_config = json.loads(config_raw)
        except IOError:
            raise ValueError('No config found!')

    def _save(self):
        with open('config.json', 'w+') as f:
            config_formatted = json.dumps(self._whole_config, indent=4)
            f.write(config_formatted)

    def get_mail_config(self) -> {str : str}:
        try:
            return self._whole_config['mail']
        except KeyError:
            raise ValueError('Mail-Config is not yet configured!')

    def set_mail_config(self, config: {str: str}):
        self._whole_config.update({'mail': config})
        self._save()

    def get_token(self) -> str:
        try:
            return self._whole_config['token']
        except KeyError:
            raise ValueError('A token is not yet configured!')

    def set_token(self, token: str):
        self._whole_config.update({'token': token})
        self._save()

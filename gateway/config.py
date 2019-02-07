import os
import json


class Config(object):
    """
    This class is responsible for keeping track of the state of the web app, and
    saving and loading this state from disk.
    """
    def __init__(self, common):
        self.c = common
        self.c.log('Config.__init__', 'init')

        self.config_path = '/data/config.json'

        self._default_config = {
            'admin_onion': None,
            'user_onions': {}
        }

        self.load()

    def load(self):
        if not os.path.exists(self.config_path):
            self.c.log('Config.__init__', 'no config.json, creating a new one')
            self.config = dict(self._default_config)
            self.save()
        else:
            self.c.log('Config.__init__', 'loading config.json')
            with open(self.config_path) as f:
                self.config = json.load(f)

    def save(self):
        self.c.log('Config.__init__', 'saving config.json')
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f)

    def get(self, key):
        return self.config[key]

    def set(self, key, val):
        self.config[key] = val
        self.save()

import os
import json
import sys
class Config:
    def __init__(self, parser, config_path: str = r'~/.fastchatgpt/'):
        self.config_path = os.path.expanduser(config_path)
        self.parser = parser
        self.data = vars(parser.parse_known_args()[0]) if parser.parse_known_args()[0] is not None else {}
        self.prepare_config()
        self.read_config()

    def prepare_config(self):
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path, exist_ok=True)
        if not os.path.exists(os.path.join(self.config_path, self.data['config'])):
            with open(os.path.join(self.config_path, self.data['config']), 'w') as f:
                json.dump(self.data, f)

    def save_config(self):
        with open(os.path.join(self.config_path, self.data['config']), 'w') as f:
            json.dump(self.data, f)

    def read_config(self):
        with open(os.path.join(self.config_path, self.data['config']), 'r') as f:
            for key, value in json.load(f).items():
                if "--" + key not in sys.argv:
                    self.data[key] = value

    def set(self, key, value):
        if (key in self.data.keys() and value != self.data[key]) or key not in self.data.keys():
            self.data[key] = value
            self.save_config()

    def config_exist(self):
        return os.path.exists(os.path.join(self.config_path, self.data['config']))

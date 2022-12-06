import os

def prepare_config(path="~/.fastchatgpt", config_name="config", config_data=None):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    
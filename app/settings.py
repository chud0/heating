import pathlib

import yaml
from common import load_module

# todo: use schema for validate and work with struct object, marshmallow for ex


def load_settings(settings_path: pathlib.Path):
    settings = yaml.load(settings_path.read_text(), Loader=yaml.Loader)

    plugins_for_run = [load_module(pl) for pl in settings['plugins']]
    settings['plugins_for_run'] = plugins_for_run
    return settings

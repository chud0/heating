import importlib
import pathlib

import yaml

# todo: use schema for validate and work with struct object, marshmallow for ex


def load_settings(settings_path: pathlib.Path):
    settings = yaml.load(settings_path.read_text(), Loader=yaml.Loader)

    plugins_for_run = [_load_plugin(pl) for pl in settings['plugins']]
    settings['plugins_for_run'] = plugins_for_run
    return settings


def _load_plugin(spec: str):
    module, plugin_class = spec.rsplit('.', 1)
    loaded_module = importlib.import_module(module)
    return getattr(loaded_module, plugin_class)

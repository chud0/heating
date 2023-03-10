import importlib


def load_module(spec: str):
    module, obj = spec.rsplit('.', 1)
    loaded_module = importlib.import_module(module)
    return getattr(loaded_module, obj)

import logging
import pathlib

from plugins import PluginRunManager
from settings import load_settings

if __name__ == '__main__':
    # todo: move logging config to settings
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    app_settings = load_settings(pathlib.Path('../settings.yaml'))

    program_manager = PluginRunManager(
        plugins=app_settings['plugins_for_run'],
        plugins_settings=app_settings['plugins'],
    )
    program_manager.start()

    try:
        program_manager.run()
    except (Exception, KeyboardInterrupt):
        program_manager.stop()

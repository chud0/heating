import logging
import time
from queue import Empty, Queue
from typing import List, Type

from plugins import EventExchange
from plugins.mqtt import BaseEventPlugin, MqttPlugin
from plugins.underfloor_heating_mixer import UnderFloorHeatingMixerPlugin

plugins_for_run = [MqttPlugin, UnderFloorHeatingMixerPlugin]


# fixme: move to settings module
class Settings:
    def __init__(self, mqtt_host):
        self.mqtt_host = mqtt_host
        self.underfloor_heating_mixer = {
            'main_mixer': {
                'temp_topic': '',
                'device_topic': '',
                'target_temp': 23,
            },
            'slave_mixers': [
                {
                    'temp_topic': '',
                    'device_topic': '',
                    'target_temp': 23,
                },
                {
                    'temp_topic': '',
                    'device_topic': '',
                    'target_temp': 23,
                },
                {
                    'temp_topic': '',
                    'device_topic': '',
                    'target_temp': 23,
                },
                {
                    'temp_topic': '',
                    'device_topic': '',
                    'target_temp': 23,
                },
                {
                    'temp_topic': '',
                    'device_topic': '',
                    'target_temp': 23,
                },
            ],
            'pump': {'device_topic': '', 'state_changed_timeout': 30},
        }


class PluginRunManager:
    def __init__(self, plugins: List[Type[BaseEventPlugin]], plugins_settings):
        self._plugins = [
            p(
                event_exchange=EventExchange(incoming_message_queue=Queue(), outgoing_message_queue=Queue()),
                settings=plugins_settings,
            )
            for p in plugins
        ]

    def start(self):
        for plugin in self._plugins:
            plugin.start()

    def run(self):
        while True:
            for plugin in self._plugins:
                try:
                    event = plugin.event_exchange.get()
                except Empty:
                    continue

                for p in self._plugins:
                    if p is plugin:
                        continue

                    p.event_exchange.put(event)

            time.sleep(0.1)

    def stop(self):
        for plugin in self._plugins:
            plugin.stop()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    settings = Settings(mqtt_host='127.0.0.1')
    program_manager = PluginRunManager(plugins=plugins_for_run, plugins_settings=settings)
    program_manager.start()

    try:
        program_manager.run()
    except (Exception, KeyboardInterrupt):
        program_manager.stop()

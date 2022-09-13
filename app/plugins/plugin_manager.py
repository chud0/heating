import time
from queue import Empty, Queue
from typing import List, Type

from plugins import EventExchange
from plugins.mqtt import BaseEventPlugin


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

    def step(self):
        for plugin in self._plugins:
            self.send_out_plugin_events(plugin)

    def run(self):
        while True:
            self.step()
            time.sleep(0.1)

    def stop(self):
        # WARNING! very important keep this behavior!
        # first plugin mast bi start earlier and stop
        for plugin in self._plugins:
            plugin.stop()
            self.send_out_plugin_events(plugin)

    def send_out_plugin_events(self, plugin):
        while True:
            try:
                event = plugin.event_exchange.get()
            except Empty:
                break

            for p in self._plugins:
                if p is plugin:
                    continue

                p.event_exchange.put(event)

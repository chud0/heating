import unittest
import unittest.mock

import messages
from plugins import BaseEventPlugin, PluginRunManager


class PluginWithSendMessageOnStop(BaseEventPlugin):
    def stop(self):
        self.send_event(messages.BaseEvent())
        super().stop()

    def tick(self) -> None:
        pass


class PluginWithReceiveMessage(BaseEventPlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_event_handler(messages.BaseEvent, self.settings['test_handler'])

    def tick(self) -> None:
        pass


class TestPluginRunManager(unittest.TestCase):
    def setUp(self):
        self.event_handler_mock = unittest.mock.Mock()

        self.test_manager = PluginRunManager(
            plugins=[PluginWithReceiveMessage, PluginWithSendMessageOnStop],
            plugins_settings={'.PluginWithReceiveMessage': {'test_handler': self.event_handler_mock}},
        )

    def test_ok(self):
        self.test_manager.start()
        self.test_manager.step()
        self.test_manager.stop()

        self.event_handler_mock.assert_called()

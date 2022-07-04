import unittest
import unittest.mock

from plugins import BasePlugin


class TestBasePlugin(unittest.TestCase):
    def setUp(self):
        self.test_plugin = BasePlugin(tick_timeout=0.0001)
        self.tick_mock = unittest.mock.Mock()
        self.test_plugin.tick = self.tick_mock

    def test_ok(self):
        inner_mock = unittest.mock.Mock()
        self.test_plugin._inner_tick = inner_mock

        self.test_plugin.start()
        self.test_plugin.join()

        inner_mock.assert_called_once()
        self.tick_mock.assert_called_once()

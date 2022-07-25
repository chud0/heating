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
        self.test_plugin._before_tick = inner_mock

        self.test_plugin.start()
        self.test_plugin.join()

        inner_mock.assert_called_once()
        self.tick_mock.assert_called_once()

    def test_error_on_tick(self):
        self.tick_mock.side_effect = KeyError('foo')

        with self.assertLogs(level='ERROR') as cm:
            self.test_plugin.start()
            self.test_plugin.join()

        logs = cm.output
        self.assertEqual(1, len(logs))

        log = logs[0]
        self.assertIn(f'On run tick:', log)
        self.assertIn(f'foo', log)

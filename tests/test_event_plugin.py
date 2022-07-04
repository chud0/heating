import unittest
import unittest.mock
from queue import Queue

from messages import BaseEvent
from plugins import BaseEventPlugin


class TestEvent(BaseEvent):
    pass


class TestEventPlugin(unittest.TestCase):
    def setUp(self):
        self.queue = Queue()
        self.test_plugin = BaseEventPlugin(event_queue=self.queue)

    def test_ok(self):
        event = BaseEvent()
        handler = unittest.mock.Mock()
        self.test_plugin.add_event_handler(BaseEvent, handler)
        self.queue.put_nowait(event)

        self.test_plugin._inner_tick()

        handler.assert_called_once_with(event)

    def test_error_in_event_handler(self):
        event = BaseEvent()
        handler = unittest.mock.Mock(side_effect=KeyError('foo'), name='broken_handler')
        self.test_plugin.add_event_handler(BaseEvent, handler)
        self.queue.put_nowait(event)

        with self.assertLogs(level='ERROR') as cm:
            self.test_plugin._inner_tick()

        logs = cm.output
        self.assertEqual(1, len(logs))

        log = logs[0]
        self.assertIn(f'On handle event {event}', log)
        self.assertIn(f'by handler {handler}', log)
        self.assertIn(f'foo', log)

        handler.assert_called_once_with(event)

    def test_run_all_handler_if_first_broken(self):
        event = BaseEvent()

        handlers = list()
        handlers.append(unittest.mock.Mock(side_effect=KeyError('foo'), name='broken_handler'))
        handlers.extend([unittest.mock.Mock() for _ in range(10)])
        for h in handlers:
            self.test_plugin.add_event_handler(BaseEvent, h)

        self.queue.put_nowait(event)

        with self.assertLogs(level='ERROR'):
            self.test_plugin._inner_tick()

        for h in handlers:
            h.assert_called_once_with(event)

    def test_no_handle_other_type_registered(self):
        other_type_event = BaseEvent()
        handler = unittest.mock.Mock()
        self.test_plugin.add_event_handler(TestEvent, handler)
        self.queue.put_nowait(other_type_event)

        self.test_plugin._inner_tick()

        handler.assert_not_called()

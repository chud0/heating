import unittest
import unittest.mock
from queue import Queue

from messages import BaseEvent
from plugins import BaseEventPlugin, EventExchange, handle_event


class TestEvent(BaseEvent):
    pass


class TestEventPlugin(unittest.TestCase):
    def setUp(self):
        self.event_exchange = EventExchange(incoming_message_queue=Queue(), outgoing_message_queue=Queue())
        self.test_plugin = BaseEventPlugin(event_exchange=self.event_exchange)

    def test_ok(self):
        event = BaseEvent()
        handler = unittest.mock.Mock()
        self.test_plugin.add_event_handler(BaseEvent, handler)
        self.event_exchange.put(event)

        self.test_plugin._before_tick()

        handler.assert_called_once_with(event)

    def test_send_message(self):
        event = BaseEvent()
        self.test_plugin.send_event(event)

        incoming_message = self.event_exchange.get()
        self.assertIs(event, incoming_message)

    def test_error_in_event_handler(self):
        event = BaseEvent()
        handler = unittest.mock.Mock(side_effect=KeyError('foo1'), name='broken_handler')
        self.test_plugin.add_event_handler(BaseEvent, handler)
        self.event_exchange.put(event)

        with self.assertLogs(level='ERROR') as cm:
            self.test_plugin._before_tick()

        logs = cm.output
        self.assertEqual(1, len(logs))

        log = logs[0]
        self.assertIn(f'On handle event {event}', log)
        self.assertIn(f'by handler {handler}', log)
        self.assertIn(f'foo1', log)

        handler.assert_called_once_with(event)

    def test_run_all_handler_if_first_broken(self):
        event = BaseEvent()

        handlers = list()
        handlers.append(unittest.mock.Mock(side_effect=KeyError('foo'), name='broken_handler'))
        handlers.extend([unittest.mock.Mock() for _ in range(10)])
        for h in handlers:
            self.test_plugin.add_event_handler(BaseEvent, h)

        self.event_exchange.put(event)

        with self.assertLogs(level='ERROR'):
            self.test_plugin._before_tick()

        for h in handlers:
            h.assert_called_once_with(event)

    def test_no_handle_other_type_registered(self):
        other_type_event = BaseEvent()
        handler = unittest.mock.Mock()
        self.test_plugin.add_event_handler(TestEvent, handler)
        self.event_exchange.put(other_type_event)

        self.test_plugin._before_tick()

        handler.assert_not_called()


class DummyEventPlugin(BaseEventPlugin):
    def tick(self) -> None:
        pass

    # @handle_event(BaseEvent)
    def resend_message(self, event):
        self.send_event(event)


class TestHandleEventDeco(unittest.TestCase):
    def setUp(self):
        self.event_exchange = EventExchange(incoming_message_queue=Queue(), outgoing_message_queue=Queue())
        self.test_plugin = DummyEventPlugin(event_exchange=self.event_exchange)

    @unittest.skip('before repair')
    def test_ok(self):
        event = BaseEvent()
        self.event_exchange.put(event)

        self.test_plugin._before_tick()

        incoming_message = self.event_exchange.get()
        self.assertIs(event, incoming_message)

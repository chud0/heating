import unittest.mock

from messages.events import MqttMessageSend, MqttSubscribe

from .mocks import TimeModulePatcher


class TimeMockTestMixin(unittest.TestCase):
    module_reference = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.time_patch = unittest.mock.patch(self.module_reference, new_callable=TimeModulePatcher)

    def setUp(self):
        super().setUp()
        self.time_mock: TimeModulePatcher = self.time_patch.start()

    def tearDown(self) -> None:
        super().tearDown()
        self.time_patch.stop()


class TestDeviceMixin(unittest.TestCase):
    def setUp(self) -> None:
        self._test_device = None

        super().setUp()

    @property
    def test_device(self):
        if self._test_device:
            return self._test_device
        raise NotImplementedError('Not implemented test_device')

    @test_device.setter
    def test_device(self, value):
        self._test_device = value

    def assert_device_enabled(self, device=None, msg='Device is not enabled'):
        device = device or self.test_device
        self.assertTrue(device.enabled, msg=msg)

    def assert_device_disabled(self, device=None, msg='Device is not disabled'):
        device = device or self.test_device
        self.assertFalse(device.enabled, msg=msg)

    def assert_device_turned_on(self, device=None, msg=None):
        device = device or self.test_device
        self.assertTrue(device.turned_on, msg=msg)

    def assert_device_turned_off(self, device=None, msg=None):
        device = device or self.test_device
        self.assertFalse(device.turned_on, msg=msg)

    def assert_device_need_work(self, device=None, msg=None):
        device = device or self.test_device
        self.assertTrue(device.is_need_work, msg=msg)

    def assert_device_not_need_work(self, device=None, msg=None):
        device = device or self.test_device
        self.assertFalse(device.is_need_work, msg=msg)

    def assert_subscribe_message(self, message, topic):
        self.assertTrue(isinstance(message, MqttSubscribe), msg=f'Message must be MqttSubscribe, not <{type(message)}>')
        self.assertEqual(topic, message.topic, msg=f'Topic must be equal to <{topic}>')

    def assert_turn_on_device_message(self, message, topic=None, msg=None):
        self.assertTrue(isinstance(message, MqttMessageSend), msg=msg)
        self.assertEqual('1', message.payload, msg=msg)
        if topic:
            self.assertEqual(topic, message.topic, msg=msg)

    def assert_turn_on_device_messages(self, messages, topic=None, msg=None):
        self.assertEqual(1, len(messages), msg=msg)
        turn_on_message = messages[0]
        self.assert_turn_on_device_message(turn_on_message, topic=topic, msg=msg)

    def assert_turn_off_device_message(self, message, topic=None, msg=None):
        self.assertTrue(isinstance(message, MqttMessageSend), msg=msg)
        self.assertEqual('0', message.payload, msg=msg)
        if topic:
            self.assertEqual(topic, message.topic, msg=msg)

    def assert_turn_off_device_messages(self, messages, topic=None, msg=None):
        self.assertEqual(1, len(messages), msg=msg)
        turn_off_message = messages[0]
        self.assert_turn_off_device_message(turn_off_message, topic=topic, msg=msg)

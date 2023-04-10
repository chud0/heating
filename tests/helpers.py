import time
import unittest.mock

# from messages.events import MqttMessageSend


class TimeModulePatcher:
    def __init__(self):
        self.start_test_time = self.current_test_time = time.time()

    def time(self):
        return self.current_test_time

    def sleep(self, seconds: float):
        self.current_test_time += seconds

    @property
    def test_duration(self):
        return self.current_test_time - self.start_test_time

    def turn_time_forward(self, seconds: float):
        return self.sleep(seconds)

    def __getattr__(self, item):
        raise NotImplementedError(f'Not implemented method {item}')


class TimeMockTestMixin(unittest.TestCase):
    module_reference = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.time_patch = unittest.mock.patch(self.module_reference, new_callable=TimeModulePatcher)

    def setUp(self):
        self.time_mock: TimeModulePatcher = self.time_patch.start()

    def tearDown(self) -> None:
        self.time_patch.stop()


class TestDeviceMixin(unittest.TestCase):
    def setUp(self) -> None:
        self._test_device = None

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

    def assert_messages_turn_on_device(self, messages, topic, msg=None):
        self.assertEqual(1, len(messages), msg=msg)

        turn_on_message = messages[0]
        self.assertIsInstance(turn_on_message, MqttMessageSend, msg=msg)
        self.assertEqual('1', turn_on_message.payload, msg=msg)

        if topic:
            self.assertEqual(topic, turn_on_message.topic, msg=msg)

    def assert_messages_turn_off_device(self, messages, topic=None, msg=None):
        self.assertEqual(1, len(messages), msg=msg)

        turn_off_message = messages[0]
        self.assertIsInstance(turn_off_message, MqttMessageSend, msg=msg)
        self.assertEqual('0', turn_off_message.payload, msg=msg)

        if topic:
            self.assertEqual(topic, turn_off_message.topic, msg=msg)

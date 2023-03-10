import logging
import time
import unittest
import unittest.mock
from typing import List

from devices import thermostat


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
        raise NotImplementedError()


class TestThermostatDevice(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.time_patch = unittest.mock.patch('devices.thermostat.time', new_callable=TimeModulePatcher)

    def setUp(self):
        self.test_device = thermostat.Thermostat(name='a', hardware_topic='test', target_temperature=23, hysteresis=1)

        self.time_mock: TimeModulePatcher = self.time_patch.start()

    def tearDown(self) -> None:
        self.time_patch.stop()

    def assert_messages_not_change_state_device(self, messages):
        self.assertEqual(0, len(messages))

    def assert_messages_turn_on_device(self, messages):
        self.assertEqual(1, len(messages))
        self.assertEqual('1', messages[0].payload)

    def assert_messages_turn_off_device(self, messages):
        self.assertEqual(1, len(messages))
        self.assertEqual('0', messages[0].payload)

    def assert_device_enabled(self):
        self.assertTrue(self.test_device.enabled)

    def assert_device_disabled(self):
        self.assertFalse(self.test_device.enabled)

    def assert_words_in(self, container: List[str], member: str):
        for word in container:
            self.assertIn(word, member)

    def send_temp_to_device(self, temp: float, forward_seconds: float = 1):
        self.time_mock.turn_time_forward(forward_seconds)
        return self.test_device(temp)

    def test_on_to_target(self):
        self.assert_device_disabled()

        # turn on, after run; 23 > 21
        messages = self.send_temp_to_device(21, forward_seconds=0)
        self.assert_messages_turn_on_device(messages)
        self.assert_device_enabled()

        # stay enabled; 23 > 22
        messages = self.send_temp_to_device(22, forward_seconds=5)
        self.assert_messages_not_change_state_device(messages)

        # turn off; 23 == 23
        messages = self.send_temp_to_device(23, forward_seconds=5)
        self.assert_messages_turn_off_device(messages)
        self.assert_device_disabled()

    def test_turn_off_on_temp_quick_get_up(self):
        # 0.5 on 1 second max
        self.send_temp_to_device(10, forward_seconds=0)
        self.assert_device_enabled()

        with self.assertLogs(level=logging.WARNING) as cm:
            messages = self.send_temp_to_device(10.5, forward_seconds=1)
        self.assert_words_in(['quick', 'temp'], cm.output[0])

        self.assert_messages_turn_off_device(messages)
        self.assert_device_disabled()

    def test_enabled_when_hysteresis_zone_and_temp_get_down(self):
        self.send_temp_to_device(25, forward_seconds=0)
        self.assert_device_disabled()

        messages = self.send_temp_to_device(24.1)
        self.assert_messages_not_change_state_device(messages)

        messages = self.send_temp_to_device(24)
        self.assert_messages_turn_on_device(messages)

import logging
import unittest.mock
from typing import List

from devices import thermostat
from messages.events import MqttMessageReceived

from tests.common import TestDeviceMixin, TimeMockTestMixin


class TestThermostatDevice(TimeMockTestMixin, TestDeviceMixin, unittest.TestCase):
    module_reference = 'devices.thermostat.time'

    def setUp(self):
        super().setUp()

        self.test_device = thermostat.Thermostat(
            name='test_thermo',
            hardware_topic='hw_topic',
            sensor_topic='sens_topic',
            target_temperature=23,
            hysteresis=1,
        )
        self.test_device.enable()

    def assert_messages_not_change_state_device(self, messages):
        self.assertEqual(0, len(messages))

    def assert_words_in(self, container: List[str], member: str):
        for word in container:
            self.assertIn(word, member)

    def send_temp_to_device(self, temp: float, device=None, forward_seconds: float = 1):
        device = device or self.test_device
        self.time_mock.turn_time_forward(forward_seconds)
        return device.on_sensor_data_receive(MqttMessageReceived(topic='test', payload=str(temp)))

    def test_on_to_target(self):
        """ test up to target and turn off """
        self.assert_device_turned_off()

        # turn on, after run; 23 > 21
        messages = self.send_temp_to_device(21, forward_seconds=0)
        self.assert_turn_on_device_messages(messages)
        self.assert_device_turned_on()

        # stay enabled; 23 > 22
        messages = self.send_temp_to_device(22, forward_seconds=5)
        self.assert_messages_not_change_state_device(messages)

        # turn off; 23 == 23
        messages = self.send_temp_to_device(23, forward_seconds=5)
        self.assert_turn_off_device_messages(messages)
        self.assert_device_turned_off()

    def test_turn_off_on_temp_quick_get_up(self):
        # 0.5 on 1 second max
        self.send_temp_to_device(10, forward_seconds=0)
        self.assert_device_turned_on()

        with self.assertLogs(level=logging.WARNING) as cm:
            messages = self.send_temp_to_device(10.5, forward_seconds=1)
        self.assert_words_in(['quick', 'temp'], cm.output[0])

        self.assert_turn_off_device_messages(messages)
        self.assert_device_turned_off()

    def test_enabled_when_hysteresis_zone_and_temp_get_down(self):
        self.send_temp_to_device(25, forward_seconds=0)
        self.assert_device_turned_off()

        messages = self.send_temp_to_device(24.1)
        self.assert_messages_not_change_state_device(messages)

        messages = self.send_temp_to_device(24)
        self.assert_turn_on_device_messages(messages)
        self.assert_device_turned_on()

import unittest

from devices import thermostat


class TestThermostatDevice(unittest.TestCase):
    def setUp(self):
        self.test_device = thermostat.Thermostat(hardware_topics=['test'], target_temperature=23, hysteresis=1)

    def assert_messages_for_do_not_change_state_device(self, messages):
        self.assertEqual(0, len(messages))

    def assert_messages_for_turn_on_device(self, messages):
        self.assertEqual(1, len(messages))
        self.assertEqual('1', messages[0].payload)

    def assert_messages_for_turn_off_device(self, messages):
        self.assertEqual(1, len(messages))
        self.assertEqual('0', messages[0].payload)

    def test_ok(self):
        """
        test: start for warming, fast up, inertial with hysteresis, stop on set target
        # todo: split on several small
        """
        self.assertFalse(self.test_device.enabled)

        messages = self.test_device(21)
        self.assert_messages_for_turn_on_device(messages)
        self.assertTrue(self.test_device.enabled)

        messages = self.test_device(21.5)
        self.assert_messages_for_do_not_change_state_device(messages)

        # very fast temp up - device turn off
        messages = self.test_device(23)
        self.assert_messages_for_turn_off_device(messages)
        self.assertFalse(self.test_device.enabled)

        messages = self.test_device(24)
        self.assert_messages_for_do_not_change_state_device(messages)

        messages = self.test_device(22)
        self.assert_messages_for_turn_on_device(messages)
        self.assertTrue(self.test_device.enabled)

        # turn off for compensation inertial
        messages = self.test_device(22.5)
        self.assert_messages_for_turn_off_device(messages)
        self.assertFalse(self.test_device.enabled)

        messages = self.test_device(23)
        self.assert_messages_for_turn_on_device(messages)
        self.assertTrue(self.test_device.enabled)

        messages = self.test_device(23.5)
        self.assert_messages_for_turn_off_device(messages)
        self.assertFalse(self.test_device.enabled)

        messages = self.test_device(23.7)
        self.assert_messages_for_turn_on_device(messages)
        self.assertTrue(self.test_device.enabled)

        # stop up temp with hysteresis
        messages = self.test_device(24.5)
        self.assert_messages_for_turn_off_device(messages)
        self.assertFalse(self.test_device.enabled)

        # cycle run again
        messages = self.test_device(21)
        self.assert_messages_for_turn_on_device(messages)
        self.assertTrue(self.test_device.enabled)

import unittest

from devices import thermostat


class TestThermostatDevice(unittest.TestCase):
    def setUp(self):
        self.test_device = thermostat.Thermostat(hardware_topic='test', target_temperature=23, hysteresis=1)

    def assert_messages_for_do_not_change_state_device(self, messages):
        self.assertEqual(0, len(messages))

    def assert_messages_for_turn_on_device(self, messages):
        self.assertEqual(1, len(messages))
        self.assertEqual(True, messages[0].payload)

    def assert_messages_for_turn_off_device(self, messages):
        self.assertEqual(1, len(messages))
        self.assertEqual(False, messages[0].payload)

    def test_ok(self):
        """
        temper  21 22 23 24 25 26 25 24 23 22 21
        message  +  *  *  *  -  *  *  *  *  *  +
        enabled  +  +  +  +  -  -  -  -  -  -  +
        """
        self.assertFalse(self.test_device.enabled)

        messages = self.test_device(21)
        self.assert_messages_for_turn_on_device(messages)
        self.assertTrue(self.test_device.enabled)

        messages = self.test_device(22)
        self.assert_messages_for_do_not_change_state_device(messages)

        messages = self.test_device(23)
        self.assert_messages_for_do_not_change_state_device(messages)

        messages = self.test_device(24)
        self.assert_messages_for_do_not_change_state_device(messages)

        messages = self.test_device(25)
        self.assert_messages_for_turn_off_device(messages)
        self.assertFalse(self.test_device.enabled)

        messages = self.test_device(26)
        self.assert_messages_for_do_not_change_state_device(messages)

        messages = self.test_device(25)
        self.assert_messages_for_do_not_change_state_device(messages)

        messages = self.test_device(24)
        self.assert_messages_for_do_not_change_state_device(messages)

        messages = self.test_device(23)
        self.assert_messages_for_do_not_change_state_device(messages)

        messages = self.test_device(22)
        self.assert_messages_for_do_not_change_state_device(messages)

        messages = self.test_device(21)
        self.assert_messages_for_turn_on_device(messages)
        self.assertTrue(self.test_device.enabled)

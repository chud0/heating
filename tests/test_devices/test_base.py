import unittest.mock

import errors
from devices import BaseDevice

from tests.helpers import TestDeviceMixin, TimeMockTestMixin


class TestBaseDevice(TimeMockTestMixin, TestDeviceMixin, unittest.TestCase):
    module_reference = 'devices._base.time'

    def test_base_create(self):
        device = BaseDevice(name='test', hardware_topic='hardware_topic')

        self.assert_device_disabled(device, msg='Must be disabled after creation')
        self.assert_device_turned_off(device, msg='Must be turned off after creation')
        self.assert_device_not_need_work(device, msg='Not work if device disabled')

    def test_base_enable(self):
        device = BaseDevice(name='test', hardware_topic='hardware_topic')

        enable_msg = device.enable()
        self.assertEqual([], enable_msg, msg='Must be no messages if device not turned on')
        self.assert_device_enabled(device, msg='Must be enabled after enable() call')

        om_enable_msg = device.enable()
        self.assertEqual([], om_enable_msg, msg='Must be no messages if device enabled now')

    def test_base_disable(self):
        device = BaseDevice(name='test', hardware_topic='hardware_topic')

        device.enable()
        disable_msg = device.disable()
        self.assertEqual([], disable_msg, msg='Must be no messages if device not turned on')
        self.assert_device_disabled(device, msg='Must be disabled after disable() call')

        om_disable_msg = device.disable()
        self.assertEqual([], om_disable_msg, msg='Must be no messages if device disabled now')

    def test_turn_on_disabled_device(self):
        device = BaseDevice(name='test', hardware_topic='hardware_topic')

        with self.assertRaises(errors.DeviceDisabledError):
            device.turn_on()

        device.enable()
        device.turn_on()
        self.assert_device_turned_on(device, msg='Must be turned enabled device after turn_on() call')

    def test_get_topics_subscriptions(self):
        device_without_sensor = BaseDevice(name='test', hardware_topic='hardware_topic')
        self.assertEqual(device_without_sensor.get_topics_subscriptions(), [])

        device_with_sensor = BaseDevice(name='test', hardware_topic='hardware_topic', sensor_topic='sensor_topic')
        self.assertEqual(
            device_with_sensor.get_topics_subscriptions(),
            [('sensor_topic', device_with_sensor.on_sensor_data_receive)],
        )

    def test_need_work(self):
        device = BaseDevice(name='without_dep', hardware_topic='hardware_topic')
        device.enable()
        self.assert_device_need_work(device, msg='Enabled device without dependencies ready to be turned on')

        device_with_dependencies = BaseDevice(name='with_dep', hardware_topic='hardware_topic', dependencies=[device])
        device_with_dependencies.enable()
        self.assert_device_not_need_work(
            device_with_dependencies,
            msg='Device with dependencies must be not need work if dependencies not turned on')

        device.turn_on()
        self.assert_device_need_work(
            device_with_dependencies,
            msg='Device with dependencies must be need work if dependencies turned on')

        device_with_dependencies_delay = BaseDevice(
            name='with_dep_delay', hardware_topic='hardware_topic', dependencies=[device], state_changed_timeout=10)
        device_with_dependencies_delay.enable()
        self.assert_device_need_work(
            device_with_dependencies_delay,
            msg='Device with dependencies and delay must be need work if dependencies turned on')

        device.turn_off()
        for _ in range(9):
            self.time_mock.sleep(1)
            self.assert_device_need_work(
                device_with_dependencies_delay,
                msg='Device wait state_changed_timeout')

        self.time_mock.sleep(1)
        self.assert_device_not_need_work(
            device_with_dependencies_delay,
            msg='timeout has come')

    def test_on_sensor_data_receive(self):
        device = BaseDevice(name='test', hardware_topic='hardware_topic', sensor_topic='sensor_topic')
        device.on_sensor_data_receive(None)
        self.assertEqual(self.time_mock.time(), device.last_sensor_time)

        self.time_mock.sleep(10)
        self.assertEqual(self.time_mock.time() - 10, device.last_sensor_time)




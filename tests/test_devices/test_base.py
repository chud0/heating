import logging
import unittest
import unittest.mock
from typing import List

import errors
from devices import BaseDevice

from .helpers import TimeModulePatcher


class TimeMockTestMixin:
    module_reference = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.time_patch = unittest.mock.patch(self.module_reference, new_callable=TimeModulePatcher)

    def setUp(self):
        self.time_mock: TimeModulePatcher = self.time_patch.start()

    def tearDown(self) -> None:
        self.time_patch.stop()


class TestBaseDevice(TimeMockTestMixin, unittest.TestCase):
    module_reference = 'devices._base.time'

    def test_base_create(self):
        device = BaseDevice(name='test', hardware_topic='hardware_topic')

        self.assertFalse(device.enabled, msg='Must be disabled after creation')
        self.assertFalse(device.turned_on, msg='Must be turned off after creation')
        self.assertFalse(device.is_need_work, msg='Not work if device disabled')

    def test_base_enable(self):
        device = BaseDevice(name='test', hardware_topic='hardware_topic')

        enable_msg = device.enable()
        self.assertEqual([], enable_msg, msg='Must be no messages if device not turned on')
        self.assertTrue(device.enabled, msg='Must be enabled after enable() call')

        om_enable_msg = device.enable()
        self.assertEqual([], om_enable_msg, msg='Must be no messages if device enabled now')

    def test_base_disable(self):
        device = BaseDevice(name='test', hardware_topic='hardware_topic')

        device.enable()
        disable_msg = device.disable()
        self.assertEqual([], disable_msg, msg='Must be no messages if device not turned on')
        self.assertFalse(device.enabled, msg='Must be disabled after disable() call')

        om_disable_msg = device.disable()
        self.assertEqual([], om_disable_msg, msg='Must be no messages if device disabled now')

    def test_turn_on_disabled_device(self):
        device = BaseDevice(name='test', hardware_topic='hardware_topic')

        with self.assertRaises(errors.DeviceDisabledError):
            device.turn_on()

        device.enable()
        device.turn_on()
        self.assertTrue(device.turned_on)

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
        self.assertTrue(device.is_need_work, msg='Device without dependencies must be need work if device turned on')

        device_with_dependencies = BaseDevice(name='with_dep', hardware_topic='hardware_topic', dependencies=[device])
        device_with_dependencies.enable()
        self.assertFalse(
            device_with_dependencies.is_need_work,
            msg='Device with dependencies must be not need work if dependencies not turned on')

        device.turn_on()
        self.assertTrue(
            device_with_dependencies.is_need_work,
            msg='Device with dependencies must be need work if dependencies turned on')

        device_with_dependencies_delay = BaseDevice(
            name='with_dep_delay', hardware_topic='hardware_topic', dependencies=[device], state_changed_timeout=10)
        device_with_dependencies_delay.enable()
        self.assertTrue(
            device_with_dependencies_delay.is_need_work,
            msg='Device with dependencies and delay must be need work if dependencies turned on')

        device.turn_off()
        for _ in range(9):
            self.time_mock.sleep(1)
            self.assertTrue(
                device_with_dependencies_delay.is_need_work,
                msg='Device wait state_changed_timeout')

        self.time_mock.sleep(1)
        self.assertFalse(
            device_with_dependencies_delay.is_need_work,
            msg='timeout has come')

    def test_on_sensor_data_receive(self):
        device = BaseDevice(name='test', hardware_topic='hardware_topic', sensor_topic='sensor_topic')
        device.on_sensor_data_receive(None)
        self.assertEqual(self.time_mock.time(), device.last_sensor_time)

        self.time_mock.sleep(10)
        self.assertEqual(self.time_mock.time() - 10, device.last_sensor_time)




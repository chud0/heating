import unittest.mock
from queue import Empty, Queue

import yaml
from messages.events import MqttMessageReceived, MqttMessageSend, MqttSubscribe
from plugins import EventExchange, UnderFloorHeatingMixerPlugin

from tests.common import TestDeviceMixin, TimeMockTestMixin


class TestUnderFloorHeatingMixerPlugin(TestDeviceMixin, TimeMockTestMixin, unittest.TestCase):
    module_reference = 'devices.thermostat.time'

    def assert_exchange_empty(self, exchange):
        self.assertTrue(exchange.is_empty(), msg='Exchange must be empty')

    def build_plugin_with_devices(self, devices: str):
        """
        :param devices: in yaml format
        """
        devices = yaml.load(devices, Loader=yaml.FullLoader)
        settings = {
            '.UnderFloorHeatingMixerPlugin': {
                'devices': devices
            }
        }
        event_exchange = EventExchange(incoming_message_queue=Queue(), outgoing_message_queue=Queue())
        plugin = UnderFloorHeatingMixerPlugin(
            event_exchange=event_exchange,
            settings=settings,
        )
        return plugin, event_exchange

    def test_plugin_base(self):
        # start\stop test
        plugin, _ = self.build_plugin_with_devices(devices='{}')

        plugin.start()
        plugin.stop()

    def test_start_procedure(self):
        # subscribe, device enable, ...
        devices = """
        devices.thermostat.Thermostat:
          - name: without_dependency
            sensor_topic: sensor_test
            hardware_topic: hardware_test
            target_temperature: 25
        """
        plugin, event_exchange = self.build_plugin_with_devices(devices=devices)

        subscribe_msg = event_exchange.get()
        self.assert_subscribe_message(subscribe_msg, 'sensor_test')
        self.assert_exchange_empty(event_exchange)

    def test_start_with_dependency(self):
        """
        Проверка старта плагина с устройствами, зависящими от других устройств.
        Устройства должны подписаться на топики сенсоров зависимых устройств.
        """
        devices = """
        devices.thermostat.Thermostat:
          - name: without_dependency
            sensor_topic: whd_sensor
            hardware_topic: whd_hardware_test
            target_temperature: 25
          - name: with_dependency
            sensor_topic: wd_sensor
            hardware_topic: wd_hardware_test
            target_temperature: 25
            dependencies: [without_dependency]
          - name: om_with_dependency
            sensor_topic: om_wd_sensor
            hardware_topic: om_wd_hardware_test
            target_temperature: 25
            dependencies: [with_dependency]
        """
        plugin, event_exchange = self.build_plugin_with_devices(devices=devices)

        # subscribe without_dependency device
        self.assert_subscribe_message(event_exchange.get(), 'whd_sensor')

        # subscribe with_dependency device
        self.assert_subscribe_message(event_exchange.get(), 'wd_sensor')
        self.assert_subscribe_message(event_exchange.get(), 'whd_sensor')

        # subscribe om_with_dependency device
        self.assert_subscribe_message(event_exchange.get(), 'om_wd_sensor')
        self.assert_subscribe_message(event_exchange.get(), 'wd_sensor')
        self.assert_subscribe_message(event_exchange.get(), 'whd_sensor')
        self.assert_exchange_empty(event_exchange)

    def test_plugin_with_dependency_devices(self):
        """
        Тест на проверку работы плагина с устройствами, зависящими от других устройств.
        При включении устройства с зависимостью, включаются все устройства от которых оно зависит.
        При выключении устройства с зависимостью, выключаются все устройства которые от него зависят.
        """
        devices = """
        devices.thermostat.Thermostat:
          - name: without_dependency
            sensor_topic: whd_sensor
            hardware_topic: whd_hardware_test
            target_temperature: 25
          - name: with_dependency
            sensor_topic: wd_sensor
            hardware_topic: wd_hardware_test
            target_temperature: 25
            dependencies: [without_dependency]
        devices.pump.Pump:
          - name: pump
            hardware_topic: pmp_hardware_test
            dependencies: [with_dependency]
        """
        plugin, event_exchange = self.build_plugin_with_devices(devices=devices)

        # subscribe to sensor and dependencies sensors. don't check it here
        while not event_exchange.is_empty():
            event_exchange.get()

        # put message for turn on devices, check turn on device with dependency
        event_exchange.put(MqttMessageReceived(topic='whd_sensor', payload='25'))
        event_exchange.put(MqttMessageReceived(topic='wd_sensor', payload='25'))
        plugin._before_tick()

        without_dependencies_device_msg = event_exchange.get()
        self.assert_turn_on_device_message(without_dependencies_device_msg, 'whd_hardware_test')
        with_dependencies_device_msg = event_exchange.get()
        self.assert_turn_on_device_message(with_dependencies_device_msg, 'wd_hardware_test')
        pump_device_msg = event_exchange.get()
        self.assert_turn_on_device_message(pump_device_msg, 'pmp_hardware_test')
        self.assert_exchange_empty(event_exchange)

        for dv in plugin.devices:
            self.assert_device_turned_on(dv)

        plugin.tick()

        self.time_mock.turn_time_forward(5)
        event_exchange.put(MqttMessageReceived(topic='whd_sensor', payload='26'))

        plugin._before_tick()

        without_dependencies_device_msg = event_exchange.get()
        self.assert_turn_off_device_message(without_dependencies_device_msg, 'whd_hardware_test')
        with_dependencies_device_msg = event_exchange.get()
        self.assert_turn_off_device_message(with_dependencies_device_msg, 'wd_hardware_test')
        pump_device_msg = event_exchange.get()
        self.assert_turn_off_device_message(pump_device_msg, 'pmp_hardware_test')
        self.assert_exchange_empty(event_exchange)

        for dv in plugin.devices:
            self.assert_device_turned_off(dv)

import unittest.mock
from queue import Empty, Queue

from messages.events import MqttMessageReceived, MqttMessageSend, MqttSubscribe
from plugins import EventExchange, UnderFloorHeatingMixerPlugin

from tests.common import TimeMockTestMixin


class TestUnderFloorHeatingMixerPlugin(TimeMockTestMixin, unittest.TestCase):
    module_reference = 'devices.thermostat.time'

    def assert_turn_on_device_message(self, message, topic):
        self.assertTrue(isinstance(message, MqttMessageSend))
        self.assertEqual('1', message.payload)
        self.assertEqual(topic, message.topic)

    def assert_turn_off_device_message(self, message, topic):
        self.assertTrue(isinstance(message, MqttMessageSend))
        self.assertEqual('0', message.payload)
        self.assertEqual(topic, message.topic)

    def assert_device_turned_on(self, device):
        self.assertTrue(device.turned_on, msg='Device must be turned on')

    def assert_device_turned_off(self, device):
        self.assertFalse(device.turned_on, msg='Device must be turned off')

    def assert_exchange_empty(self, exchange):
        self.assertTrue(exchange.is_empty())

    def build_plugin_with_devices(self, devices):
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
        plugin, _ = self.build_plugin_with_devices(devices={})

        plugin.start()
        plugin.stop()

    def test_start_procedure(self):
        # subscribe, device enable, ...
        devices = {
            'devices.thermostat.Thermostat':
                [
                    {
                        'name': 'without_dependecy',
                        'sensor_topic': 'sensor_test',
                        'hardware_topic': 'hardware_test',
                        'target_temperature': 25,
                    },
                ],
        }

        plugin, event_exchange = self.build_plugin_with_devices(devices=devices)

        subscribe_msg = event_exchange.get()
        self.assertTrue(isinstance(subscribe_msg, MqttSubscribe))
        self.assertEqual(subscribe_msg.topic, 'sensor_test')
        self.assert_exchange_empty(event_exchange)

    def test_plugin_with_dependency_devices(self):
        """
        Тест на проверку работы плагина с устройствами, зависящими от других устройств.
        При включении устройства с зависимостью, включаются все устройства от которых оно зависит.
        При выключении устройства с зависимостью, выключаются все устройства которые от него зависят.
        """
        devices = {
            'devices.thermostat.Thermostat':
                [
                    {
                        'name': 'with_dependecy',
                        'sensor_topic': 'wd_sensor',
                        'hardware_topic': 'wd_hardware_test',
                        'target_temperature': 25,
                        'dependencies': ['without_dependecy'],
                    },
                    {
                        'name': 'without_dependecy',
                        'sensor_topic': 'whd_sensor',
                        'hardware_topic': 'whd_hardware_test',
                        'target_temperature': 25,
                    },
                ],
            'devices.pump.Pump':
                [
                    {
                        'name': 'pump',
                        'hardware_topic': 'pmp_hardware_test',
                        'dependencies': ['with_dependecy'],
                    },
                ],
        }

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

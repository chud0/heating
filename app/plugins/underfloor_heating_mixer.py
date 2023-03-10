import logging
import time
from collections import defaultdict
from functools import partial

import common
import devices
import messages

from ._base_message_handlers import BaseMqttMessagePlugin

logger = logging.getLogger(__name__)


class UnderFloorHeatingMixerPlugin(BaseMqttMessagePlugin):
    # todo: remove salve\main mixer, add required device:
    #   - main mixer add to required all flor mixers
    #   - pump add to required main mixer
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._plugin_devices = []

        self.load_devices()

    def load_devices(self):
        if self._plugin_devices:
            raise ValueError('Plugin devices loaded!')

        devices_settings = self.settings['devices']
        for device_spec, device_params in devices_settings.items:
            device_temp_topic = device_params.pop('temp_topic', None)
            device_class = common.load_module(device_spec)
            device = device_class(**device_params)

            self._plugin_devices.append(device)
            if device_temp_topic is not None:
                self.subscribe_to_topic(
                    device_temp_topic,
                    partial(self._handle_receive_temperature, device=device),
                )

    def _handle_sensor_data_event(self, event: messages.events.MqttMessageReceived, device: devices.Thermostat):
        self.send_events(events_to_send)

    def tick(self) -> None:
        # todo check all devices and send messages
        pass

    def stop(self):
        for dv in self._plugin_devices:
            self.send_events(dv.stop())

        super(UnderFloorHeatingMixerPlugin, self).stop()

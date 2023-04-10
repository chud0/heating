import logging
from collections import defaultdict

import devices
import messages

from ._base_message_handlers import BaseMqttMessagePlugin

logger = logging.getLogger(__name__)


def build_device_message_sender(device_cb, send_method):
    def device_message_sender(event: messages.events.MqttMessageReceived):
        event_messages = device_cb(event)
        send_method(event_messages)

    return device_message_sender


class UnderFloorHeatingMixerPlugin(BaseMqttMessagePlugin):
    # todo: Rename to "DevicePlugin"
    # todo: validate and wrap to struct plugins settings

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._plugin_devices = devices.DeviceLoader(self.settings['devices']).load_devices()
        for device in self._plugin_devices:
            for topic, cb in device.get_topics_subscriptions():
                handler = build_device_message_sender(cb, self.send_events)
                self.subscribe_to_topic(topic, handler)

            device.enable()

    @property
    def devices(self):
        return self._plugin_devices[:]

    def tick(self) -> None:
        for dv in self._plugin_devices:
            self.send_events(dv())

    def stop(self):
        for dv in self.devices:
            self.send_events(dv.disable())

        super(UnderFloorHeatingMixerPlugin, self).stop()

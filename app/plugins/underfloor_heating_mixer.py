import logging
from collections import defaultdict

import devices
import messages

from ._base_message_handlers import BaseMqttMessagePlugin

logger = logging.getLogger(__name__)


class UnderFloorHeatingMixerPlugin(BaseMqttMessagePlugin):
    # todo: validate and wrap to struct plugins settings

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._plugin_devices = devices.DeviceLoader(self.settings['devices']).load_devices()

        # subscribe devices to sensors
        self._topics_to_handler_map = defaultdict(list)
        topic_subscribed = set()  # dont duplicate device subscribe

        for device in self._plugin_devices:
            for topic, cb in device.get_topics_subscriptions():
                self._topics_to_handler_map[topic].append(cb)

                if topic not in topic_subscribed:
                    self.subscribe_to_topic(topic, self.device_message_handler)
                    topic_subscribed.add(topic)

    def device_message_handler(self, event: messages.events.MqttMessageReceived):
        for cb in self._topics_to_handler_map[event.topic]:
            self.send_events(cb(event))

    def tick(self) -> None:
        # todo check all devices and send messages
        pass

    def stop(self):
        for dv in self._plugin_devices:
            self.send_events(dv.stop())

        super(UnderFloorHeatingMixerPlugin, self).stop()

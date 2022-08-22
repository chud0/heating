import logging
from collections import defaultdict

import messages

from ._base import BaseEventPlugin

logger = logging.getLogger(__name__)


MIXER_TEMP_SENSOR_MQTT_TOPIC = 'home/lights/sitting_room'


class MqttMessagePlugin(BaseEventPlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._mqtt_message_router_map = defaultdict(list)
        self.add_event_handler(messages.events.MqttMessageReceived, self._mqtt_message_router_event_handler)

    def _mqtt_message_router_event_handler(self, event: messages.events.MqttMessageReceived):
        logger.info('Handle event %s', event)
        for event_handler in self._mqtt_message_router_map[event.topic]:
            try:
                event_handler(event)
            except Exception as ex:
                logger.error('On handle event %s error %s', event, ex)

    def subscribe_to_topic(self, topic: str, message_handler):
        self._mqtt_message_router_map[topic].append(message_handler)
        self.event_exchange.send_message(messages.events.MqttSubscribe(topic, 1))


class UnderFloorHeatingMixerPlugin(MqttMessagePlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscribe_to_topic(MIXER_TEMP_SENSOR_MQTT_TOPIC, self.mixer_temp_sensor_handler)

    def mixer_temp_sensor_handler(self, event: messages.events.MqttMessageReceived):
        logger.info('On mixer temp handler. Temp %s', event.payload)

    def tick(self) -> None:
        pass

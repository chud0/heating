import logging

import messages
from ._base_message_handlers import BaseMqttMessagePlugin

logger = logging.getLogger(__name__)


MIXER_TEMP_SENSOR_MQTT_TOPIC = 'home/lights/sitting_room'


class UnderFloorHeatingMixerPlugin(BaseMqttMessagePlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscribe_to_topic(MIXER_TEMP_SENSOR_MQTT_TOPIC, self.mixer_temp_sensor_handler)

    def mixer_temp_sensor_handler(self, event: messages.events.MqttMessageReceived):
        logger.info('On mixer temp handler. Temp %s', event.payload)

    def tick(self) -> None:
        pass

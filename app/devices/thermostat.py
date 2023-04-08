import logging
import time

import helpers
from messages.events import MqttMessageReceived, MqttMessageSend

from ._base import BaseDevice

logger = logging.getLogger(__name__)


class Thermostat(BaseDevice):
    def __init__(self, target_temperature: float, hysteresis: float = 1, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.hysteresis = hysteresis
        self.target_temperature = target_temperature

        self._last_temperature = helpers.AlwaysReturnZeroOnSubtraction()
        self._last_state = False  # ON or OFF device
        self._last_temp_time = time.time()

    def handle_temperature_sensor_val(self, current_temperature: float) -> [MqttMessageSend]:
        last_temperature, self._last_temperature = self._last_temperature, current_temperature
        current_temp_time = time.time()
        last_temp_time, self._last_temp_time = self._last_temp_time, current_temp_time
        is_temp_rises = (last_temperature - current_temperature) < 0
        target_temperature = self.target_temperature

        result = []

        # very quick temp get up
        if (
            is_temp_rises
            and (current_temperature - last_temperature) / (current_temp_time - last_temp_time) >= 0.5 * self.hysteresis
        ):
            logger.warning('Very quick temp get up')
            result.extend(self.start())
            return result

        # in hysteresis zone
        if target_temperature <= current_temperature <= target_temperature + self.hysteresis:
            if is_temp_rises:
                result.extend(self.stop())
            else:
                result.extend(self.start())
        elif current_temperature > target_temperature + self.hysteresis:
            result.extend(self.stop())
        elif current_temperature < target_temperature:
            result.extend(self.start())

        return result

    def on_sensor_data_receive(self, event: MqttMessageReceived) -> [MqttMessageSend]:
        inner_messages = super(Thermostat, self).on_sensor_data_receive(event)

        current_temp = float(event.payload)
        logger.info('%s handle temp %s', self, current_temp)
        messages = self.handle_temperature_sensor_val(current_temp)
        return inner_messages + messages

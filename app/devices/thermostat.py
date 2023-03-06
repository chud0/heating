import logging

import helpers
from messages.events import MqttMessageSend
import time

from ._base import BaseMqttDevice


logger = logging.getLogger(__name__)


class Thermostat(BaseMqttDevice):
    def __init__(self, target_temperature: float, hysteresis: float = 1, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.hysteresis = hysteresis
        self.target_temperature = target_temperature

        self._last_temperature = helpers.AlwaysReturnZeroOnSubtraction()
        self._last_state = False  # ON or OFF device
        self._last_temp_time = time.time()

        self._enabled = True

    def __call__(self, current_temperature: float) -> [MqttMessageSend]:
        last_temperature, self._last_temperature = self._last_temperature, current_temperature
        current_temp_time = time.time()
        last_temp_time, self._last_temp_time = self._last_temp_time, current_temp_time
        is_temp_rises = (last_temperature - current_temperature) < 0
        target_temperature = self.target_temperature

        result = []
        if not self._enabled:
            return result

        # very quick temp get up
        if is_temp_rises and (current_temperature - last_temperature) >= (0.5 * self.hysteresis / (current_temp_time - last_temp_time)):
            logger.warning('Very quick temp get up')
            result.extend(self.turn_off())
            return result

        # in hysteresis zone
        if target_temperature <= current_temperature <= target_temperature + self.hysteresis:
            if is_temp_rises:
                result.extend(self.turn_off())
            else:
                result.extend(self.turn_on())
        elif current_temperature > target_temperature + self.hysteresis:
            result.extend(self.turn_off())
        elif current_temperature < target_temperature:
            result.extend(self.turn_on())

        return result

    def start(self) -> [MqttMessageSend]:
        # do not send messages now, only on need in process
        super(Thermostat, self).start()
        return []

    def stop(self) -> [MqttMessageSend]:
        device_stopping_messages = super(Thermostat, self).stop()

        self._last_state = False  # enabled attr required for this, and not generate stopping messages
        return device_stopping_messages

    @property
    def enabled(self):
        # device controller
        return self._last_state

    def turn_on(self):
        # hardware device
        if self.enabled:
            return []
        self._last_state = True
        return self._build_messages_turn_on()

    def turn_off(self):
        # hardware device
        if not self.enabled:
            return []
        self._last_state = False
        return self._build_messages_turn_off()

import helpers
from messages.events import MqttMessageSend

from ._base import BaseMqttDevice


class Thermostat(BaseMqttDevice):
    def __init__(self, target_temperature: float, hysteresis: float = 1, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.hysteresis = hysteresis
        self.target_temperature = target_temperature

        self._last_temperature = helpers.AlwaysReturnZeroOnSubtraction()
        self._last_state = False  # ON or OFF device

        self._enabled = True

    def __call__(self, current_temperature: float) -> [MqttMessageSend]:
        last_temperature, self._last_temperature = self._last_temperature, current_temperature
        result = []
        if not self._enabled:
            return result

        if current_temperature - last_temperature > self.hysteresis / 2:
            # very quick up
            result.extend(self.turn_off())
            return result

        target_temperature = self.target_temperature
        if self._last_state:
            # on getting hot now
            target_temperature -= self.hysteresis

            if target_temperature >= current_temperature:
                # nothing to do, hardware enabled now
                return result

            result.extend(self.turn_off())

        else:
            target_temperature += self.hysteresis

            if target_temperature <= current_temperature:
                # nothing to do, hardware disabled now
                return result

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

from messages.events import MqttMessageSend

from ._base import BaseMqttDevice


class Thermostat(BaseMqttDevice):
    def __init__(self, target_temperature: float, hysteresis: float = 1, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.hysteresis = hysteresis
        self.target_temperature = target_temperature

        self._last_temperature = 0
        self._last_state = False  # ON or OFF device

        self._enabled = True

    def __call__(self, current_temperature: float) -> [MqttMessageSend]:
        result = []
        if not self._enabled:
            return result

        target_temperature = self.target_temperature
        if self._last_state:
            # on getting hot now
            target_temperature += self.hysteresis

            if target_temperature >= current_temperature:
                # nothing to do, hardware enabled now
                return result

            self._last_state = False
            result.extend(self._build_messages_turn_off())

        else:
            target_temperature -= self.hysteresis

            if target_temperature <= current_temperature:
                # nothing to do, hardware disabled now
                return result

            self._last_state = True
            result.extend(self._build_messages_turn_on())

        return result

    def start(self) -> [MqttMessageSend]:
        # do not send messages now, only on need in process
        super(Thermostat, self).start()
        return []

    def stop(self) -> [MqttMessageSend]:
        self._last_state = False
        return super(Thermostat, self).stop()

    @property
    def enabled(self):
        return self._last_state

from messages import events


class Thermostat:
    def __init__(self, hardware_topic: str, target_temperature: float, hysteresis: float = 1):
        self._hardware_topic = hardware_topic
        self.hysteresis = hysteresis
        self.target_temperature = target_temperature

        self._last_temperature = 0
        self._last_state = False  # ON or OFF device

        self.is_working = True

        self._cmd_turn_on, self._cmd_turn_off = True, False

    def __call__(self, current_temperature: float):
        result = []
        if not self.is_working:
            return result

        target_temperature = self.target_temperature
        if self._last_state:
            # on getting hot now
            target_temperature += self.hysteresis

            if target_temperature >= current_temperature:
                # nothing to do, hardware enabled now
                return result

            self._last_state = False
            result.append(events.MqttMessageSend(topic=self._hardware_topic, payload=self._cmd_turn_off))

        else:
            target_temperature -= self.hysteresis

            if target_temperature <= current_temperature:
                # nothing to do, hardware disabled now
                return result

            self._last_state = True
            result.append(events.MqttMessageSend(topic=self._hardware_topic, payload=self._cmd_turn_on))

        return result

    def start(self):
        self.is_working = True

    def stop(self):
        self.is_working = False

    @property
    def enabled(self):
        return self._last_state

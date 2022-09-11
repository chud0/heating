from messages import events


class Pump:
    def __init__(self, hardware_topic: str):
        self._hardware_topic = hardware_topic
        self._cmd_turn_on, self._cmd_turn_off = True, False
        self.enabled = False

    def start(self):
        if self.enabled:
            return []

        self.enabled = True
        return [events.MqttMessageSend(topic=self._hardware_topic, payload=self._cmd_turn_on)]

    def stop(self):
        if not self.enabled:
            return []

        self.enabled = False
        return [events.MqttMessageSend(topic=self._hardware_topic, payload=self._cmd_turn_off)]

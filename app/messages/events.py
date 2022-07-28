class BaseEvent:
    pass


class MqttEvents(BaseEvent):
    pass


class MqttSubscribe(MqttEvents):
    def __init__(self, topic, qos=0, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.topic = topic
        self.qos = qos


class MqttMessageReceived(MqttEvents):
    def __init__(self, topic, payload, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.topic = topic
        self.payload = payload


class MqttMessageSend(MqttEvents):
    def __init__(self, topic, payload, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.topic = topic
        self.payload = payload

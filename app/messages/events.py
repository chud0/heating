class BaseEvent:
    pass


class MqttEvents(BaseEvent):
    pass


class MqttSubscribe(MqttEvents):
    def __init__(self, topic, qos=0, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.topic = topic
        self.qos = qos

    def __repr__(self):
        return f'{self.__class__.__name__}({self.topic}, {self.qos})'


class MqttMessageReceived(MqttEvents):
    def __init__(self, topic, payload, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.topic = topic
        self.payload = payload

    def __repr__(self):
        return f'{self.__class__.__name__}({self.topic}, {self.payload})'


class MqttMessageSend(MqttEvents):
    def __init__(self, topic, payload, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.topic = topic
        self.payload = payload

    def __repr__(self):
        return f'{self.__class__.__name__}({self.topic}, {self.payload})'

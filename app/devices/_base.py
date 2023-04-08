import abc
import logging
import time
import typing

from messages.events import MqttMessageReceived, MqttMessageSend

logger = logging.getLogger(__name__)


class AbstractDevice(abc.ABC):
    @abc.abstractmethod
    def start(self) -> typing.List[typing.Any]:
        ...

    @abc.abstractmethod
    def stop(self) -> typing.List[typing.Any]:
        ...

    @property
    @abc.abstractmethod
    def enabled(self):
        ...

    @abc.abstractmethod
    def __call__(self, *args, **kwargs) -> typing.List[MqttMessageSend]:
        ...


class BaseMqttDevice(AbstractDevice):
    # hardware_topic и sensor_topic can have one value, if you need to change it -
    #     make the type of device/sensor: topic value

    _cmd_turn_on = '1'
    _cmd_turn_off = '0'

    def __init__(self, name: str, hardware_topic: str, sensor_topic: str = None):
        self._hardware_topic = hardware_topic
        self._sensor_topic = sensor_topic

        self._enabled = False
        self.name = name

    def _build_messages_for_mqtt_send(self, payload: str) -> typing.List[MqttMessageSend]:
        return [MqttMessageSend(topic=self._hardware_topic, payload=payload)]

    def _build_messages_turn_on(self) -> typing.List[MqttMessageSend]:
        return self._build_messages_for_mqtt_send(self._cmd_turn_on)

    def _build_messages_turn_off(self) -> typing.List[MqttMessageSend]:
        return self._build_messages_for_mqtt_send(self._cmd_turn_off)

    def start(self) -> typing.List[MqttMessageSend]:
        if self.enabled:
            return []

        logger.info('Starting device %s', self)
        self._enabled = True
        return self._build_messages_turn_on()

    def stop(self) -> typing.List[MqttMessageSend]:
        if not self.enabled:
            return []

        logger.info('Stopping device %s', self)
        self._enabled = False
        return self._build_messages_turn_off()

    def __call__(self, *args, **kwargs) -> typing.List[MqttMessageSend]:
        return []

    @property
    def enabled(self):
        return self._enabled

    def get_topics_subscriptions(self):
        if not self._sensor_topic:
            return []
        return [(self._sensor_topic, self.on_sensor_data_receive)]

    def __str__(self):
        return f'{self.__class__.__name__}[{self.name}]'

    def on_sensor_data_receive(self, event: MqttMessageReceived) -> [MqttMessageSend]:
        logger.warning('Receive event %s on default, callback. Register a handler to process the message')


class BaseDevice(BaseMqttDevice):
    def __init__(self, dependencies: ['BaseDevice'] = None, state_changed_timeout=0, *args, **kwargs):
        super(BaseDevice, self).__init__(*args, **kwargs)

        self._dependencies = dependencies
        self.state_changed_timeout = state_changed_timeout
        self._last_sensor_time = time.time()

    @property
    def dependencies_enabled(self):
        return any((d.enabled for d in self._dependencies))

    def on_sensor_data_receive(self, event: MqttMessageReceived) -> [MqttMessageSend]:
        self._last_sensor_time = time.time()
        return []

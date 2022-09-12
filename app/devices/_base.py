import abc
import logging
import typing

from messages.events import MqttMessageSend


logger = logging.getLogger(__name__)


class BaseDevice(abc.ABC):
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
    def __call__(self, *args, **kwargs) -> typing.List[typing.Any]:
        ...


class BaseMqttDevice(BaseDevice):
    _cmd_turn_on = '1'
    _cmd_turn_off = '0'

    def __init__(self, hardware_topics: typing.List[str], name: str = None):
        self._hardware_topics = hardware_topics
        self._enabled = False

        self._name = name or 'unnamed'

    def _build_messages_for_mqtt_send(self, payload: str) -> typing.List[MqttMessageSend]:
        return [MqttMessageSend(topic=topic, payload=payload) for topic in self._hardware_topics]

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

    def __str__(self):
        return f'{self.__class__.__name__}[{self._name}]'

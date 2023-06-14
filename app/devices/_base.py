import abc
import logging
import time
import typing

import errors
from messages.events import MqttMessageReceived, MqttMessageSend

logger = logging.getLogger(__name__)


class AbstractDevice(abc.ABC):
    """
    Base class for all devices
    enable/disable - this is a common device switch, will it turn on
    start/stop - this is the activity of the device, is it doing active work now
    """

    @abc.abstractmethod
    def enable(self) -> typing.List[typing.Any]:
        ...

    @abc.abstractmethod
    def disable(self) -> typing.List[typing.Any]:
        ...

    @property
    @abc.abstractmethod
    def enabled(self):
        ...

    @abc.abstractmethod
    def turn_on(self) -> typing.List[typing.Any]:
        ...

    @abc.abstractmethod
    def turn_off(self) -> typing.List[typing.Any]:
        ...

    @property
    @abc.abstractmethod
    def turned_on(self):
        ...

    @abc.abstractmethod
    def __call__(self, *args, **kwargs) -> typing.List[MqttMessageSend]:
        ...


class BaseAbstractMqttDevice(AbstractDevice, abc.ABC):
    # hardware_topic и sensor_topic can have one value, if you need to change it -
    #     make the type of device/sensor: topic value

    _cmd_turn_on = '1'
    _cmd_turn_off = '0'

    def __init__(self, hardware_topic: str, sensor_topic: str = None):
        self._hardware_topic = hardware_topic
        self._sensor_topic = sensor_topic

        self._turned_on = False
        self.last_sensor_time = time.time()

    @property
    def turned_on(self):
        return self._turned_on

    @turned_on.setter
    def turned_on(self, value: bool):
        if value and not self.enabled:
            raise errors.DeviceDisabledError(f'Device {self} is disabled, can not turn on')
        self._turned_on = value

    @property
    def sensor_topic(self):
        return self._sensor_topic

    def turn_on(self) -> typing.List[MqttMessageSend]:
        if self.turned_on:
            return []

        logger.info('Turn on device %s', self)
        self.turned_on = True
        return self._build_messages_turn_on()

    def turn_off(self) -> typing.List[MqttMessageSend]:
        if not self.turned_on:
            return []

        logger.info('Turn off %s', self)
        self.turned_on = False
        return self._build_messages_turn_off()

    def __call__(self, *args, **kwargs) -> typing.List[MqttMessageSend]:
        return []

    def get_topics_subscriptions(self):
        if not self._sensor_topic:
            return []
        return [(self._sensor_topic, self.on_sensor_data_receive)]

    def on_sensor_data_receive(self, event: MqttMessageReceived) -> [MqttMessageSend]:
        self.last_sensor_time = time.time()
        return []

    def _build_messages_for_mqtt_send(self, payload: str) -> typing.List[MqttMessageSend]:
        return [MqttMessageSend(topic=self._hardware_topic, payload=payload)]

    def _build_messages_turn_on(self) -> typing.List[MqttMessageSend]:
        return self._build_messages_for_mqtt_send(self._cmd_turn_on)

    def _build_messages_turn_off(self) -> typing.List[MqttMessageSend]:
        return self._build_messages_for_mqtt_send(self._cmd_turn_off)


class BaseDevice(BaseAbstractMqttDevice):
    """
    do not work without dependencies
    """

    def __init__(self, name: str, dependencies: ['BaseDevice'] = None, state_changed_timeout=0, *args, **kwargs):
        super(BaseDevice, self).__init__(*args, **kwargs)

        self.name = name
        self._dependencies = dependencies or []

        self._enabled = False
        self.state_changed_timeout = state_changed_timeout

        self._last_dependencies_turned_on_time = time.time()

    def get_topics_subscriptions(self):
        """
        Здесь устройство подписывается на топики сенсоров устройств от которых зависит, для того чтобы обработать
        события вместе с ними. Обработка идет после выполнения в зависимых устройствах, для того чтобы учесть изменения
        их состояний.
        """
        subscription = super().get_topics_subscriptions()
        topics_for_subscriptions = {t for t, _ in subscription}
        for dv in self._dependencies:
            for topic, _ in dv.get_topics_subscriptions():
                if topic in topics_for_subscriptions:
                    continue
                subscription.append((topic, self.check_need_work_on_dependency_sensor))
                topics_for_subscriptions.add(topic)

        return subscription

    def check_need_work_on_dependency_sensor(self, _):
        if not self.is_need_work:
            return self.turn_off()
        return []

    @property
    def enabled(self):
        return self._enabled

    def enable(self) -> typing.List[MqttMessageSend]:
        if self._enabled:
            return []
        self._enabled = True
        return []

    def disable(self) -> typing.List[MqttMessageSend]:
        if not self._enabled:
            return []
        self._enabled = False
        return self.turn_off()

    @property
    def is_need_work(self):
        if not self._enabled:
            return False

        if not self._dependencies:
            return True

        if not self.dependencies_turned_on:
            if time.time() - self._last_dependencies_turned_on_time < self.state_changed_timeout:
                return True
            return False

        return True

    @property
    def dependencies_turned_on(self):
        is_dependencies_turned_on = any((d.turned_on for d in self._dependencies))
        if is_dependencies_turned_on:
            self._last_dependencies_turned_on_time = time.time()
        return is_dependencies_turned_on

    def __repr__(self):
        return f'{self.__class__.__name__}[{self.name}] {"+" if self.enabled else "-"}/{"+" if self.turned_on else "-"}'

import logging
import time
from abc import ABC
from collections import defaultdict
from queue import Empty, Queue
from threading import Thread
from typing import Callable, List, Type

from messages import BaseEvent

logger = logging.getLogger(__name__)


class EventExchange:
    def __init__(self, incoming_message_queue: Queue, outgoing_message_queue: Queue):
        self.incoming_message_queue = incoming_message_queue
        self.outgoing_message_queue = outgoing_message_queue

    def receive_message(self, timeout=None):
        # consumer method
        return self.incoming_message_queue.get(timeout=timeout, block=False)

    def send_message(self, event: BaseEvent, timeout=None):
        # consumer method
        return self.outgoing_message_queue.put(event, timeout=timeout, block=False)

    def put(self, event: BaseEvent, timeout=None):
        # to exchange
        return self.incoming_message_queue.put(event, timeout=timeout, block=False)

    def get(self, timeout=None):
        # from exchange
        return self.outgoing_message_queue.get(timeout=timeout, block=False)

    def __repr__(self):
        return (
            f'{self.__class__.__name__} '
            f'[{self.incoming_message_queue.qsize()} / '
            f'{self.outgoing_message_queue.qsize()}]'
        )


class BasePlugin(Thread):
    def __init__(self, tick_timeout=0.1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tick_timeout = tick_timeout

        self.is_running = True

    def run(self) -> None:
        while self.is_running:
            try:
                self._before_tick()
            except Exception as err:
                logger.exception('On run _before_tick: %s', err)

            try:
                self.tick()
            except Exception as err:
                logger.exception('On run tick: %s', err)

            try:
                self._after_tick()
            except Exception as err:
                logger.exception('On run _after_tick: %s', err)

            time.sleep(self.tick_timeout)

    def stop(self):
        logger.info('Stoping plugin %s', self)
        self.is_running = False

    def join(self, *args, **kwargs) -> None:
        self.stop()
        super().join(*args, **kwargs)

    def _before_tick(self) -> None:
        pass

    def tick(self) -> None:
        raise NotImplementedError

    def _after_tick(self) -> None:
        pass


def handle_event(event_class: Type[BaseEvent]):
    # fixme: not work it!
    def inner(handler: Callable):
        d = dir(handler)
        dct = handler.__dict__
        cls = handler.__class__
        if not getattr(cls, 'event_handlers', None):
            raise TypeError(f'{cls} not have required special object "event_handlers"')

        cls.event_handlers[event_class].append(handler)
        return handler

    return inner


class BaseEventPlugin(BasePlugin, ABC):
    def __init__(self, event_exchange: EventExchange, *args, settings=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.event_exchange = event_exchange
        self.event_handlers = defaultdict(list)

        self.settings = self._find_plugin_settings(settings)

    def _find_plugin_settings(self, all_plugins_settings):
        if not all_plugins_settings:
            return {}

        for plugin_spec in all_plugins_settings.keys():
            _, plugin_class_name = plugin_spec.rsplit('.', 1)
            if plugin_class_name == self.__class__.__name__:
                return all_plugins_settings[plugin_spec]

        logger.error('Not found settings for plugin %s', self)

    def _before_tick(self) -> None:
        while True:
            try:
                event = self.event_exchange.receive_message()
            except Empty:
                break
            else:
                self.handle_event(event)

        super()._before_tick()

    def add_event_handler(self, event_type, handler: Callable):
        self.event_handlers[event_type].append(handler)
        logger.info('Added handler %s for event type %s', handler, event_type)

    def handle_event(self, event: BaseEvent):
        logger.debug('Handle event %s', event)
        event_handlers = self.event_handlers[type(event)]
        if not event_handlers:
            logger.info('Not found handler for event %s', event)
            return

        for handler in event_handlers:
            try:
                handler(event)
            except Exception as err:
                logger.exception('On handle event %s by handler %s: %s', event, handler, err)

    def send_event(self, event: BaseEvent):
        return self.event_exchange.send_message(event)

    def send_events(self, events: List[BaseEvent]):
        result = []
        for ev in events:
            result.append(self.send_event(ev))
        return result

    def stop(self):
        # handle messages before stop
        self._before_tick()

        super().stop()

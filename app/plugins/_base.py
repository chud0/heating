import logging
import time
from collections import defaultdict
from queue import Empty, Queue
from threading import Thread
from typing import Callable

from messages import BaseEvent

logger = logging.getLogger(__name__)


class BasePlugin(Thread):
    def __init__(self, tick_timeout=0.1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tick_timeout = tick_timeout

        self.is_running = True

    def run(self) -> None:
        while self.is_running:
            try:
                self._inner_tick()
            except Exception as err:
                logger.exception('On run _inner_tick: %s', err)

            try:
                self.tick()
            except Exception as err:
                logger.exception('On run tick: %s', err)

            time.sleep(self.tick_timeout)

    def stop(self):
        self.is_running = False

    def join(self, *args, **kwargs) -> None:
        self.stop()
        super().join(*args, **kwargs)

    def _inner_tick(self) -> None:
        pass

    def tick(self) -> None:
        raise NotImplementedError


def handle_event(event_class: BaseEvent):
    def inner(plugin: BaseEventPlugin, handler: Callable):
        plugin.add_event_handler(event_class, handler)
        return handler

    return inner


class BaseEventPlugin(BasePlugin):
    def __init__(self, event_queue: Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.event_queue = event_queue
        self.event_handlers = defaultdict(list)

    def _inner_tick(self) -> None:
        while True:
            try:
                event = self.event_queue.get_nowait()
            except Empty:
                break
            else:
                self.handle_event(event)

        super()._inner_tick()

    def add_event_handler(self, event_type, handler: Callable):
        self.event_handlers[event_type].append(handler)
        logger.info('Added handler %s for event type %s', handler, event_type)

    def handle_event(self, event: BaseEvent):
        logger.info('Handle event %s', event)
        for handler in self.event_handlers[type(event)]:
            try:
                handler(event)
            except Exception as err:
                logger.exception('On handle event %s by handler %s: %s', event, handler, err)

    def tick(self) -> None:
        raise NotImplementedError

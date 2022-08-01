"""
todo: add special event on connect and disconnect
todo: whether it is necessary to save messages for sending while the client is disconnected?
todo: can work without connect to mqtt on __init__
"""
import logging
import time

import messages
import paho.mqtt.client

from ._base import BaseEventPlugin

logger = logging.getLogger(__name__)


class MqttPlugin(BaseEventPlugin):
    def __init__(self, mqtt_host, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._subscribed_to_topics = []
        self._need_subscribe_to = []
        self.add_event_handler(messages.events.MqttSubscribe, self._subscribe_event_handler)

        self._need_send_messages = []
        self.add_event_handler(messages.events.MqttMessageSend, self._send_message_event_handler)

        self.mqtt_client = paho.mqtt.client.Client()
        self.mqtt_client.on_connect = self.on_connect_callback
        self.mqtt_client.on_disconnect = self.on_disconnect_callback
        self.mqtt_client.on_message = self.on_message_receive
        self.mqtt_client.enable_logger(logger=logger)
        self.mqtt_client.connect(mqtt_host, keepalive=10)

        self._client_connected = False

    def _subscribe_event_handler(self, event: messages.events.MqttSubscribe):
        self._need_subscribe_to.append((event.topic, event.qos))

    def _send_message_event_handler(self, event: messages.events.MqttMessageSend):
        self._need_send_messages.append((event.topic, event.payload))

    def on_connect_callback(self, client, userdata, flags, rc):
        logger.info('Connected with result code %s', rc)
        self._client_connected = True

        self.client_subscribe()

    def on_disconnect_callback(self, client, userdata, rc):
        logger.error('Mqtt disconnected!!!')
        self._client_connected = False

        self._need_subscribe_to = self._subscribed_to_topics.copy()
        self._subscribed_to_topics.clear()

    def on_message_receive(self, client, userdata, msg):
        topic, payload = msg.topic, msg.payload.decode()
        logger.info('Received message "%s" from topic "%s"', payload, topic)
        self.event_exchange.send_message(messages.events.MqttMessageReceived(topic, payload))

    def client_subscribe(self):
        while self._need_subscribe_to:
            topic_with_param = self._need_subscribe_to.pop(0)
            logger.info('Subscribe to mqtt topic %s', topic_with_param)

            self.mqtt_client.subscribe(topic_with_param)
            self._subscribed_to_topics.append(topic_with_param)

    def send_messages(self):
        while self._need_send_messages:
            topic, payload = self._need_send_messages.pop(0)
            logger.info('Send to mqtt topic "%s" message "%s"', topic, payload)

            self.mqtt_client.publish(topic, payload.encode())

    def tick(self) -> None:
        if not self._client_connected:
            logger.warning('Mqtt client disconnected. Reconnect')
            try:
                self.mqtt_client.reconnect()
            except ConnectionRefusedError:
                logger.warning('Mqtt client not connected')
                time.sleep(5)
                return

            time.sleep(1)
            self.mqtt_client.loop()

        self.client_subscribe()
        self.send_messages()

        self.mqtt_client.loop()


"""
from plugins.mqtt import MqttPlugin
from plugins import BaseEventPlugin, EventExchange
from queue import Queue
import logging
import messages

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',)
event_exchange = EventExchange(incoming_message_queue=Queue(), outgoing_message_queue=Queue())
pl = MqttPlugin('127.0.0.1', event_exchange)
pl.start()

event_exchange.put(messages.events.MqttSubscribe("home/lights/sitting_room", 1))

event_exchange.put(messages.events.MqttMessageSend("home/lights/sitting_room", '1'))
"""
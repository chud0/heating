import logging
import time

import devices
import messages

from ._base_message_handlers import BaseMqttMessagePlugin

logger = logging.getLogger(__name__)


class UnderFloorHeatingMixerPlugin(BaseMqttMessagePlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._device_by_temp_topic = {}  # topic: Thermostat
        device_settings = self.settings.underfloor_heating_mixer

        pump_settings = device_settings['pump']
        self.pump = devices.Pump(hardware_topic=pump_settings['device_topic'])
        self.last_pump_state_changed_at, self.pump_state_changed_timeout = 0, pump_settings['state_changed_timeout']

        for thermo_head_settings in device_settings['slave_mixers'] + [device_settings['main_mixer']]:
            thermostat = devices.Thermostat(
                hardware_topic=thermo_head_settings['device_topic'],
                target_temperature=thermo_head_settings['target_temp'],
            )
            self._device_by_temp_topic[thermo_head_settings['temp_topic']] = thermostat
            self.subscribe_to_topic(thermo_head_settings['temp_topic'], self.mixer_temp_sensor_handler)

    def mixer_temp_sensor_handler(self, event: messages.events.MqttMessageReceived):
        current_temp = float(event.payload)
        logger.info('On mixer temp handler. Temp %s', current_temp)
        thermostat = self._device_by_temp_topic[event.topic]
        events_to_send = thermostat(current_temp)
        for event in events_to_send:
            self.send_event(event)

    def tick(self) -> None:
        if time.time() - self.last_pump_state_changed_at < self.pump_state_changed_timeout:
            return

        pump_need_working = any(map(lambda t: t.enabled, self._device_by_temp_topic.values()))
        if pump_need_working:
            events_to_send = self.pump.start()
        else:
            events_to_send = self.pump.stop()

        for event in events_to_send:
            self.send_event(event)
            self.last_pump_state_changed_at = time.time()

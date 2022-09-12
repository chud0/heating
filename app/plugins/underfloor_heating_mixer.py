import logging
import time
from collections import defaultdict
from functools import partial

import devices
import messages

from ._base_message_handlers import BaseMqttMessagePlugin

logger = logging.getLogger(__name__)


class UnderFloorHeatingMixerPlugin(BaseMqttMessagePlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._device_by_temp_topic = defaultdict(list)  # topic: List[Thermostat]
        device_settings = self.settings.underfloor_heating_mixer

        pump_settings = device_settings['pump']
        self.pump = devices.Pump(hardware_topics=pump_settings['device_topics'])
        self.last_pump_state_changed_at, self.pump_state_changed_timeout = 0, pump_settings['state_changed_timeout']

        for thermo_head_settings in device_settings['slave_mixers'] + [device_settings['main_mixer']]:
            thermostat = devices.Thermostat(
                hardware_topics=thermo_head_settings['device_topics'],
                target_temperature=thermo_head_settings['target_temp'],
                name=thermo_head_settings['name'],
            )
            self._device_by_temp_topic[thermo_head_settings['temp_topic']].append(thermostat)
            self.subscribe_to_topic(
                thermo_head_settings['temp_topic'],
                partial(self.mixer_temp_sensor_handler, thermostat=thermostat),
            )

    @property
    def all_thermo_heads(self):
        return [th for th_list in self._device_by_temp_topic.values() for th in th_list]

    def mixer_temp_sensor_handler(self, event: messages.events.MqttMessageReceived, thermostat: devices.Thermostat):
        current_temp = float(event.payload)
        logger.info('%s handle temp %s', thermostat, current_temp)
        events_to_send = thermostat(current_temp)
        self.send_events(events_to_send)

    def tick(self) -> None:
        if time.time() - self.last_pump_state_changed_at < self.pump_state_changed_timeout:
            return

        pump_need_working = any(map(lambda t: t.enabled, self.all_thermo_heads))
        if pump_need_working:
            events_to_send = self.pump.start()
        else:
            events_to_send = self.pump.stop()

        self.send_events(events_to_send)
        self.last_pump_state_changed_at = time.time()

    def stop(self):
        self.send_events(self.pump.stop())
        for th in self.all_thermo_heads:
            self.send_events(th.stop())

        super(UnderFloorHeatingMixerPlugin, self).stop()

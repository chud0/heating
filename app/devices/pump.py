import typing

import messages.events

from ._base import BaseDevice


class Pump(BaseDevice):
    def check_need_work_on_dependency_sensor(self, _) -> typing.List[messages.events.MqttMessageSend]:
        if self.is_need_work:
            return self.turn_on()

        return self.turn_off()

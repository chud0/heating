from simple_pid import PID


class Thermostat:
    P, I, D = 1, 0, 0

    def __init__(self, target_temperature: float, hysteresis: float = 1):
        self.hysteresis = hysteresis
        self.pid = PID(self.P, self.I, self.D, setpoint=target_temperature, output_limits=(0, 100), sample_time=None)

        self.last_temperature = 0

    def __call__(self, current_temperature: float, dt=None):
        last_temperature, self.last_temperature = self.last_temperature, current_temperature

        if abs(current_temperature - last_temperature) <= self.hysteresis or \
                current_temperature > self.target_temperature:
            if self.enabled:
                self.stop()
            return 0
        else:
            if not self.enabled:
                self.start()

        return self.pid(input_=current_temperature, dt=dt)

    @property
    def target_temperature(self):
        return self.pid.setpoint

    @target_temperature.setter
    def target_temperature(self, value: float):
        self.pid.setpoint = value
        self.pid.reset()

    def start(self):
        self.pid.auto_mode = True

    def stop(self):
        self.pid.auto_mode = False

    @property
    def enabled(self):
        return self.pid.auto_mode

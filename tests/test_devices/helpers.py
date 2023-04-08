import time


class TimeModulePatcher:
    def __init__(self):
        self.start_test_time = self.current_test_time = time.time()

    def time(self):
        return self.current_test_time

    def sleep(self, seconds: float):
        self.current_test_time += seconds

    @property
    def test_duration(self):
        return self.current_test_time - self.start_test_time

    def turn_time_forward(self, seconds: float):
        return self.sleep(seconds)

    def __getattr__(self, item):
        raise NotImplementedError(f'Not implemented method {item}')

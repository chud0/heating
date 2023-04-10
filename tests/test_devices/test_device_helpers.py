import unittest.mock

from devices import helpers


class TestDeviceLoader(unittest.TestCase):
    def setUp(self) -> None:
        self.devices_params = {
            'devices._base.BaseDevice': [
                {
                    'name': 'a',
                    'hardware_topic': 'topic/a',
                    'dependencies': ['b'],
                },
                {
                    'name': 'b',
                    'hardware_topic': 'topic/b',
                },
            ],
        }

    def test_ok(self):
        loader = helpers.DeviceLoader(self.devices_params)
        devices = loader.load_devices()

        self.assertEqual(2, len(devices))
        for d, name in zip(devices, ['b', 'a']):  # order is important! dependency first
            self.assertEqual(d.name, name)

    def test_missing_ref(self):
        self.devices_params['devices._base.BaseDevice'].pop(-1)  # delete dependency
        loader = helpers.DeviceLoader(self.devices_params)

        with self.assertRaisesRegex(ValueError, 'Not found device name "b" in devices'):
            loader.load_devices()

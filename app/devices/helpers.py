import logging

import common

from ._base import BaseDevice

logger = logging.getLogger(__name__)


class DeviceLoader:
    def __init__(self, devices_params: dict):
        self._devices_params_by_device_name = {
            device_params['name']: (device_spec, device_params)
            for device_spec, devices_list_param in devices_params.items()
            for device_params in devices_list_param
        }
        self._devices_by_name = dict()

    def load_devices(self) -> [BaseDevice]:
        return [self._load_device(*params) for params in self._devices_params_by_device_name.values()]

    def _load_device(self, device_spec, device_params):
        device_name = device_params['name']
        if device_name in self._devices_by_name:
            return self._devices_by_name[device_name]

        device_dependency = [self._resolve_dependency(name) for name in device_params.get('dependencies', [])]
        device_params['dependencies'] = device_dependency
        device_class = common.load_module(device_spec)
        device: BaseDevice = device_class(**device_params)

        self._devices_by_name[device.name] = device
        logger.info('Device %s loaded', device)
        return device

    def _resolve_dependency(self, device_name):
        try:
            params_for_load_device = self._devices_params_by_device_name[device_name]
        except KeyError as ex:
            raise ValueError(f'Not found device name "{device_name}" in devices, for load as dependency') from None

        return self._load_device(*params_for_load_device)

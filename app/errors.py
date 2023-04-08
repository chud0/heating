class BaseAppError(Exception):
    """Base class for all application errors."""

    pass


class DeviceError(BaseAppError):
    """Base class for all device errors."""

    pass


class DeviceDisabledError(DeviceError):
    pass

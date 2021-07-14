class SensorError(Exception):
    def __init__(self, message='Sensor Error'):
        super().__init__(message)

class GroupError(Exception):
    def __init__(self, message='Group Error'):
        super().__init__(message)

class TempError(Exception):
    def __init__(self, message='Error with setting temp'):
        super().__init__(message)

class HvacPinError(Exception):
    def __init__(self, message='Error setting pins'):
        super().__init__(message)

class HvacUnitError(Exception):
    def __init__(self, message='Error with a HVAC unit'):
        super().__init__(message)


class BoardConnectError(Exception):
    def __init__(self, message='Error connecting with board through serial'):
        super().__init__(message)

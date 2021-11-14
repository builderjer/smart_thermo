import time

from tools import merge_dict
from exceptions import *

class GenericSensor:
    def __init__(self, id, name=None, raw_data=None):
        self._name = name or self.__class__.__name__
        self._id = id
        self._raw = [raw_data] or [{'name': name, 'host': host}]
        # self._parents = parents or None

    @property
    def id(self):
        return self._id

    @property
    def as_dict(self):
        return {
            'host': self.host,
            'name': self.name,
            'device_type': self.raw_data.get('device_type', 'g_sensor'),
            'raw': self.raw_data
        }

    @property
    def host(self):
        return self._host

    @property
    def name(self):
        return self._name

    @property
    def raw_data(self):
        data = {}
        for x in self._raw:
            merge_dict(data, x)
        return data

class TempSensor(GenericSensor):
    def __init__(self, id, control_pin, output_format=None, name='generic_temp_sensor', raw_data=None, control_type=None, differential=None):
        super().__init__(id, name, raw_data)
        self._output_format = output_format
        self._control_pin = control_pin
        self._control_type = control_type or 'A' # 'A'nalog 'D'igital
        self._differential = differential or 0
        self._temp = None

    @property
    def control_pin(self):
        return self._control_pin

    @property
    def control_type(self):
        return self._control_type

    @property
    def differential(self):
        return self._differential

    @property
    def temp(self):
        return (self._temp, self.output_format)

    @property
    def output_format(self):
        return self._output_format

class LM35(TempSensor):
    """
	Info found at https://www.ti.com/product/LM35

	The LM35 sends a voltage directly proportional to centigrade temp
	"""
    def __init__(self, id, control_pin, output_format='C', name='LM35 temp sensor', raw_data={'device_type': 'temp_sensor'}, control_type='A', differential=2):
        super().__init__(id, control_pin, output_format, name, raw_data, control_type, differential)

    @property
    def temp(self):
        return self._temp

    @temp.setter
    def temp(self, raw_value):
        self._temp = raw_value * 0.4882812
        # self._temp = (raw_value * (5000 / 1024.0)) / 10

class Test(TempSensor):
    pass

class Bigone(TempSensor):
    pass

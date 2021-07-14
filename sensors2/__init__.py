import time

from brodie_house.exceptions import *
from brodie_house.tools import merge_dict


class GenericSensor:
    def __init__(self, id, name=None, raw_data=None, socket=None):
        self._name = name or self.__class__.__name__
        self._id = id
        self._raw = [raw_data] or [{'name': name, 'host': host}]
        self._sock = socket
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
            'raw': self.raw_data,
            'socket': self.sock
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

    @property
    def sock(self):
        return self._sock

    @sock.setter
    def sock(self, socket):
        self._sock = socket


class TempSensor(GenericSensor):
    def __init__(self, id, control_pin, output_format=None, name='generic_temp_sensor', raw_data=None, control_type=None, differential=None):
        super().__init__(id, name, raw_data, socket)
        self._output_format = output_format
        self._control_pin = control_pin
        self._control_type = control_type or 'A'  # 'A'nalog 'D'igital
        self._differential = differential or 0
        self._temp = None

    @property
    def as_dict(self):
        return {
            'host': self.host,
            'name': self.name,
            'device_type': self.raw_data.get('device_type', 'g_sensor'),
            'raw': self.raw_data,
            'socket': self.sock,
            'output_format': self.output_format,
            'control_pin': self.control_pin,
            'control_type': self.control_type,
            'differential': self.differential
        }

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
        return self._temp

    @property
    def output_format(self):
        return self._output_format


class LM35(TempSensor):
    """
        Info found at https://www.ti.com/product/LM35

        The LM35 sends a voltage directly proportional to centigrade temp
        """

    def __init__(self, id, control_pin, output_format='C', name='LM35 temp sensor', raw_data={'device_type': 'temp_sensor'}, control_type='A', differential=2, socket=None):
        super().__init__(id, control_pin, output_format, name,
                         raw_data, control_type, differential, socket)

    @property
    def temp(self):
        return self._temp

    @temp.setter
    def temp(self, raw_value):
        self._temp = raw_value * 0.4882812
        if self.sock:
            self.sock.emit('change_temp', {'name': self.id, 'temp': self.temp})

from smart_thermo.tools import merge_dict

class GenericDevice:
    def __init__(self, host, name=None, raw_data=None):
        self._name = name or self.__class__.__name__
        self._host = host
        self._raw = [raw_data] or [{"name": name, "host": host}]
        self._mode = ""
        self._timer = None

    def reset(self):
        self.mode = ""
        self._timer = None
        self.turn_on()

    @property
    def as_dict(self):
        return {
            "host": self.host,
            "name": self.name,
            "device_type": self.raw_data.get("device_type", "generic"),
            "state": self.is_on,
            "raw": self.raw_data
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
    def mode(self):
        return self._mode

    @property
    def is_online(self):
        return True

    @property
    def is_on(self):
        return True

    @property
    def is_off(self):
        return not self.is_on

    # status change
    def turn_on(self):
        pass

    def turn_off(self):
        raise NotImplementedError

    def toggle(self):
        if self.is_off:
            self.turn_on()
        else:
            self.turn_off()

    def __repr__(self):
        return self.name + ":" + self.host

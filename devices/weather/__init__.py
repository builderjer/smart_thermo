import sys
import os
import time
import json
import requests
from pathlib import Path

from smart_thermo.devices import GenericDevice
from smart_thermo.tools import create_daemon, create_timer

# from devices import GenericDevice
# from tools import create_daemon, create_timer

SAVE_DIRECTORY = Path(Path.home(), '.weather')
SAVE_FILE = 'forecast.json'
KEY = '16695d723dc14d67b7802125210606'
# KEY = 'e96567303e004c3099a135401212503'
LOCATION = 'delta,co'
# LOCATION = '38.845299,%20-107.793105'
URL = f'http://api.weatherapi.com/v1/forecast.json?key={KEY}&q={LOCATION}&aqi=no&alerts=yes'

class Weather(GenericDevice):
    def __init__(self, host, name='weatherapi interface', raw_data=None,
                 socket=None, autostart=None, autosave=None):
        raw_data = raw_data or {'name': name, 'description': 'Weatherapi interface'}
        super().__init__(host, name, raw_data)
        self._sock = socket
        self._forecast = self.load_forecast()
        self._current = self.forecast.get('current')
        self._autosave = autosave or True
        self._autostart = autostart or False
        if self.autostart:
            create_daemon(self.run)

    @property
    def as_dict(self):
        return {
            "host": self.host,
            "name": self.name,
            "device_type": self.raw_data.get("device_type", "generic"),
            "state": self.is_on,
            "raw": self.raw_data,
            "autostart": self.autostart,
            "forecast": self.forecast
        }

    @property
    def sock(self):
        return self._sock

    @sock.setter
    def sock(self, socket):
        if socket != self.sock:
            self._sock = socket

    @property
    def forecast(self):
        return self._forecast

    @forecast.setter
    def forecast(self, json_file):
        self._forecast = json_file

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, json_forecast):
        json_forecast.current.condition.icon = Path(json_forecast.current.condition.icon).name
        self._current = json_forecast.current

    @property
    def autosave(self):
        return self._autosave

    @autosave.setter
    def autosave(self, value):
        if value != self.autosave and isinstance(value, bool):
            self._autosave = value

    @property
    def autostart(self):
        return self._autostart

    @autostart.setter
    def autostart(self, boolian):
        if boolian != self.autostart:
            self._autostart = boolian

    def update_forecast(self):
        forecast = requests.get(URL)
        if forecast:
            f = forecast.json()
            self.forecast = f
            self.emit_junk()

    def load_forecast(self):
        try:
            with open(Path(SAVE_DIRECTORY, SAVE_FILE), 'r') as w:
                self.forecast = json.load(w)
            self.current = self.forecast.get('current')
            self.emit_junk()
        except Exception as e:
            print(f'could not load from file:  {e}')
            self.forecast = None

    def emit_junk(self):
        if self.sock:
            self.sock.emit('current_forecast', self.forecast)
            self.sock.emit('current_weather', self.current)

    def save(self):
        def write():
            with open(Path(SAVE_DIRECTORY, SAVE_FILE), 'w') as w:
                w.write(json.dumps(self.forecast, indent=4))
        try:
            os.mkdir(SAVE_DIRECTORY)
            write()
        except OSError as e:
            try:
                write()
            except Exception as e:
                print(f'Problem saving:  {e}')

    def run(self):
        self.update_forecast()
        self.save()
        create_timer(10 * 60, self.run)

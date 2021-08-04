import sys
import time
import json
import requests
from pathlib import Path

from devices import GenericDevice
from tools import create_daemon, create_timer

SAVE_DIRECTORY = Path(Path.home(), '.weather')
SAVE_FILE = 'forecast.json'
KEY = 'e96567303e004c3099a135401212503'
LOCATION = '38.845299,%20-107.793105'
URL = f'http://api.weatherapi.com/v1/forecast.json?key={KEY}&q={LOCATION}&aqi=no&alerts=yes'

class Weather(GenericDevice):
    def __init__(self, host, name='weatherapi interface', raw_data=None, socket=None, autostart=None):
        raw_data = raw_data or {'name': name, 'description': 'Weatherapi interface'}
        super().__init__(host, name, raw_data)
        self._sock = socket
        self._forecast = None
        self._autostart = autostart or False
        if self.autostart:
            create_daemon(self.run)

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
    def autostart(self):
        return self._autostart

    @autostart.setter
    def autostart(self, boolian):
        if boolian != self.autostart:
            self._autostart = boolian

    def update_forecast(self):
        print(URL)
        forecast = requests.get(URL)
        print(forecast)
        if forecast:
            f = forecast.json()
            self.forecast = f
            print(f.get('current'))
            return f

    def save(self):
        try:
            with open()
    def run(self):
        self.update_forecast()
        create_timer(10 * 60, self.run)

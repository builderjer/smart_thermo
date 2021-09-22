import sys
import os
import time
import json
import requests
from pathlib import Path

from smart_thermo.devices import GenericDevice
from smart_thermo.tools import create_daemon, create_timer, merge_dict

# from devices import GenericDevice
# from tools import create_daemon, create_timer

SAVE_DIRECTORY = Path(Path.home(), '.weather')
SAVE_FILE = 'forecast.json'
KEY = '16695d723dc14d67b7802125210606'
# KEY = 'e96567303e004c3099a135401212503'
LOCATION = 'eckert,co'

# LOCATION = 'delta,co'
# LOCATION = '38.845299,%20-107.793105'
URL = f'http://api.weatherapi.com/v1/forecast.json?key={KEY}&q={LOCATION}&aqi=no&alerts=yes'
ICON_PATH = 'images/weather/64x64/{}/{}'

class Weather(GenericDevice):
    def __init__(self, host, name='weatherapi interface', raw_data=None,
                 socket=None, autostart=None, autosave=None):
        raw_data = raw_data or {'name': name, 'description': 'Weatherapi interface'}
        super().__init__(host, name, raw_data)
        # print(ICON_PATH.format('test', 'var'))
        self._sock = socket
        # print(len(test))
        # forecast, current = self.update_forecast()
        # forecast['condition']['icon'] = Path(forecast['condition']['icon']).name
        # self._forecast = forecast
        # current['condition']['icon'] = Path(current['condition']['icon']).name
        # self._current = current

        # self.update_forecast()
        self._forecast, self._current = self.update_forecast()


        # print()
        # print('self.current')
        # print(self.forecast['forecastday'][0]['day'])
        # print()
        # print()
        # print(self.forecast)
        self.emit_weather()
        # self._current = self.forecast.get('current')
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
        print('in current setter')
        print(json_forecast.get('condition'))
        json_forecast['condition']['icon'] = Path(json_forecast.current.condition.icon).name
        self._current = json_forecast
        print(self._current.get('condition').get('icon'))

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
        # Try to load the forecast for the day
        try:
            forecast = self.load_forecast()
            print('forecast = ', forecast)
        except Exception as e:
            print('error loading first time', e)
        if not forecast:
            print('NOPE')
            forecast = requests.get(URL)
        if forecast:
            print(forecast)
            try:
                f = forecast.json()
            except Exception as e:
                print(e)
                f = forecast
            forecast = f.get('forecast')
            current = f.get('current')
            if current.get('is_day'):
                is_day = 'day'
            else:
                is_day = 'night'
            forecast['forecastday'][0]['day']['condition']['icon'] = ICON_PATH.format(is_day, Path(forecast['forecastday'][0]['day']['condition']['icon']).name)
            current['condition']['icon'] = ICON_PATH.format(is_day, Path(current['condition']['icon']).name)
            # self.forecast = f.get('forecast')
            # self.current = f.get('current')
            # self.emit_weather()
            # print(f.get('current').get('is_day'))
            return [f.get('forecast'), f.get('current')]

    def load_forecast(self):
        try:
            with open(Path(SAVE_DIRECTORY, SAVE_FILE), 'r') as w:
                # return json.load(w)
                full = json.load(w)
                # self.forecast = full.get('forecast')
                # self.current = full.get('current')
            # self.emit_weather()
        except Exception as e:
            print(f'could not load from file:  {e}')
            # self.forecast = None
            # self.current = None
            return None

    def emit_weather(self):
        # print(self.forecast)
        if self.sock:
            self.sock.emit('current_forecast', self.forecast)
            self.sock.emit('current_weather', self.current)

    def save(self):
        def write():
            with open(Path(SAVE_DIRECTORY, SAVE_FILE), 'w') as w:
                full_forecast = {}
                current = {'current': self.current}
                merge_dict(full_forecast, current)
                merge_dict(full_forecast, self.forecast)
                w.write(json.dumps(full_forecast, indent=4))

                # w.write(json.dumps(self.forecast, indent=4))
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

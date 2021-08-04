import importlib
import sys
import time

import serial
import socketio
from smart_thermo.devices import GenericDevice
from smart_thermo.exceptions import *
from smart_thermo.sensors import *
from smart_thermo.tools import (convert_temp, create_daemon, create_timer,
                                merge_dict)
from telemetrix import telemetrix

################################
# Thermostat
THERMOSTAT_MODES = ['AUTO', 'MANUAL']
THERMOSTAT_STATES = ['OFF', 'HEAT', 'COOL', 'VENT']
SAVE_DIRECTORY = '.config/thermostat/{}_thermostat.json'

################################
# Hvac units
UNIT_TYPES = ['HEATER', 'AIRCONDITIONER', 'VENT']
UNIT_STATES = ['ON', 'OFF']
# HOST = 'replace with your own server and port number'
HOST = 'http://ziggy.ziggyhome:5000'


class Thermostat:
    def __init__(self, **kwargs):
        self._sensors = kwargs.get('sensors', {})
        groups = kwargs.get('groups')
        if groups:
            self._groups = merge_dict({'ALL': []}, groups)
        else:
            self._groups = {'ALL': []}
        self._default_area = kwargs.get('default_area', 'ALL')
        self._output_format = kwargs.get('temp_format', 'F')
        self._min_heat_temp = kwargs.get('min_heat_temp', 65)
        self._max_heat_temp = kwargs.get('max_heat_temp', 74)
        self._min_cool_temp = kwargs.get('min_cool_temp', 72)
        self._max_cool_temp = kwargs.get('max_cool_temp', 82)
        self._default_heat_temp = kwargs.get('default_heat_temp', 68)
        self._default_cool_temp = kwargs.get('default_cool_temp', 78)
        mode = kwargs.get('mode', 'AUTO')
        if mode in THERMOSTAT_MODES:
            self._mode = mode
        state = kwargs.get('state', 'OFF')
        if state in THERMOSTAT_STATES:
            self._state = state
        self._desired_temp = None
        self._save_on_exit = kwargs.get('save_on_exit', True)
        self._sock = kwargs.get('sock', None)
        print('done with init')

    @property
    def sock(self):
        return self._sock

    @sock.setter
    def sock(self, socket):
        self._sock = socket

    @property
    def sensors(self):
        return self._sensors

    @property
    def groups(self):
        return self._groups

    @property
    def default_area(self):
        return self._default_area

    @default_area.setter
    def default_area(self, group_name):
        if group_name in self.groups:
            self._default_group = group_name

    @property
    def temp_format(self):
        return self._output_format

    @property
    def min_heat_temp(self):
        return self._min_heat_temp

    @property
    def max_heat_temp(self):
        return self._max_heat_temp

    @property
    def min_cool_temp(self):
        return self._min_cool_temp

    @property
    def max_cool_temp(self):
        return self._max_cool_temp

    @property
    def default_heat_temp(self):
        return self._default_heat_temp

    @default_heat_temp.setter
    def default_heat_temp(self, new_temp):
        self._default_heat_temp = new_temp

    @property
    def default_cool_temp(self):
        return self._default_cool_temp

    @default_cool_temp.setter
    def default_cool_temp(self, new_temp):
        self.default_cool_temp = new_temp

    @property
    def desired_temp(self):
        return self._desired_temp

    @desired_temp.setter
    def desired_temp(self, new_temp):
        if new_temp:
            new_temp = int(new_temp)
        if self._desired_temp != new_temp:
            if self.state == 'OFF' or self.state == 'VENT':
                self._desired_temp = None
                raise TempError(f'Cannot set temp in {self.state} state')
            elif self.state == 'HEAT':
                minmax = (self.min_heat_temp, self.max_heat_temp)
            elif self.state == 'COOL':
                minmax = (self.min_cool_temp, self.max_cool_temp)
            # if new_temp <= minmax[1] and new_temp >= minmax[0]:
            #     self._desired_temp = new_temp
            if new_temp < minmax[0]:
                self._desired_temp = minmax[0]
                raise TempError('Trying to set temp below min temp')
            elif new_temp > minmax[1]:
                self._desired_temp = minmax[1]
                raise TempError('Trying to set temp above max temp')
            self._desired_temp = new_temp
        print(f'set desired_temp to {self.desired_temp}')

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, new_mode):
        self._mode = new_mode if new_mode != self.mode and new_mode in THERMOSTAT_MODES else self.mode

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        if new_state != self._state and new_state in THERMOSTAT_STATES:

            self._state = new_state
            if self.state == 'COOL':
                self.desired_temp = self.default_cool_temp
            elif self.state == 'HEAT':
                self.desired_temp = self.default_heat_temp
            else:
                self.desired_temp = None

    @property
    def save_on_exit(self):
        return self._save_on_exit

    @save_on_exit.setter
    def save_on_exit(self, value):
        if isinstance(value, bool) and value != self.save_on_exit:
            self._save_on_exit = value

    @property
    def as_dict(self):
        sensors = []
        groups = []
        for sensor in self.sensors.values():
            sensors.append(sensor.id)
        for group in self.groups.keys():
            groups.append(group)
        return {
            'sensors': sensors,
            'groups': groups,
            'default_area': self.default_area,
            'temp_format': self.temp_format,
            'min_heat_temp': self.min_heat_temp,
            'max_heat_temp': self.max_heat_temp,
            'min_cool_temp': self.min_cool_temp,
            'max_cool_temp': self.max_cool_temp,
            'default_heat_temp': self.default_heat_temp,
            'default_cool_temp': self.default_cool_temp,
            'desired_temp': self.desired_temp,
            'mode': self.mode,
            'state': self.state,
            'save': self.save_on_exit
        }
    ######################################
    # Sensor stuff

    def add_sensor(self, sensor, board, add_to_all=True):
        if sensor in self.sensors.values():
            raise SensorError(f'Sensor {sensor.id} exists')
        else:
            try:
                self.sensors[sensor.id] = sensor
                self._activate_sensor(sensor, board)
                if add_to_all:
                    self.add_sensor_to_group('ALL', sensor)
            except Exception as e:
                print(e)

    def _activate_sensor(self, sensor, board):
        if sensor.control_type == 'A':
            board.set_pin_mode_analog_input(
                sensor.control_pin, callback=self._update, differential=sensor.differential)
        elif sensor.control_type == 'D':
            board.set_pin_mode_digital_input(
                sensor.control_pin, callback=self._update)
        else:
            return False
        print(f'Activated sensor {sensor.id}')
        # self.get_sensor_temp(sensor.id)

    def _update(self, data):
        # print(data, 'in _update')
        for sensor in self.sensors.values():
            pin = sensor.control_pin
            # print(sensor.id, data[2])
            # pin = self.sensors[sensor.id].control_pin
            if pin == data[1] and data[2]:
                sensor.temp = data[2]
                if self.sock:
                    self.sock.emit('inside_temp_change',
                                   self.get_group_temp(self.default_area))
                # print(f'updated {sensor.id} to {sensor.temp}')

    def remove_sensor(self, sensor):
        if sensor in self.sensors:
            print(sensor, type(sensor))
            self.sensors.pop(sensor)
        else:
            raise SensorError(f'Sensor {sensor} does not exist')

    def add_sensor_to_group(self, group_name, sensor):
        if group_name in self.groups and sensor not in self.groups[group_name]:
            self.groups[group_name].append(sensor)
            return True
        elif group_name in self.groups and sensor in self.groups[group_name]:
            raise SensorError(
                f'Sensor {sensor.id} is already a member of {group_name}')
        raise GroupError(f'Group {group_name} does not exist')

    def remove_sensor_from_group(self, group_name, sensor):
        if group_name in self.groups and sensor in self.groups[group_name]:
            self.groups[group_name].remove(sensor)
        elif group_name in self.groups and sensor not in self.groups[group_name]:
            raise SensorError(
                f'Sensor {sensor.id} is not in group {group_name}')
        raise GroupError(f'Group {group_name} does not exist')

    def get_sensor_temp(self, sensor):
        """
        param: sensor
            The name of the sensor
        """
        try:
            s = self.sensors.get(sensor)
            if self.temp_format != s.output_format:
                return round(convert_temp(self.sensors[sensor].temp, self.temp_format), 2)
            return self.sensors[sensor].temp
        except Exception as e:
            print(e)

# End sensor stuff
#######################################

#######################################
# Group stuff

    def add_group(self, group_name, sensors=None):
        # TODO: allow sensors to be added on call
        """
        param: group
            Name of the group to be created
        param: sensors
            ** not used yet
            A list of sensors to add to the group
        """
        if group_name in self.groups:
            raise GroupError(f'Group {group_name} already exists')
        self.groups[group_name] = sensors or []
        return True

    def remove_group(self, group_name):
        if group_name in self.groups:
            self.groups.remove(group_name)
            return True
        raise GroupError(f'Group {group_name} does not exist')

    def get_group_sensors(self, group_name):
        try:
            group_sensors = []
            for sensor in self.groups.get(group_name):
                group_sensors.append(sensor.id)
            return group_sensors
        except Exception as e:
            print(e)

    def get_group_temp(self, group_name):
        try:
            group = self.groups.get(group_name)
            temps = []
            for sensor in group:
                sensor_temp = self.get_sensor_temp(sensor.id)
                if sensor_temp:
                    temps.append(sensor_temp)
            return round(sum(temps) / len(temps), 2)
        except Exception as e:
            print(e)
# End Group stuff
#######################################

#######################################


class HVACUnit:
    def __init__(self, unit_type, on_off_pin=None, on_pin=None, off_pin=None, state=None):
        """
        A class to control each unit of a HVAC system.
        A unit can be one of 'heater', 'airconditioner', or 'vent'
        Any other type will raise an Error

        Either onOffPin or onPin and offPin need to be set.
        Non latching relays use onOffPin,
        latching relays use both onPin and offPin

        # NOTE: My setup uses latching relays, but non-latching are suggested
        """

        if not unit_type.upper() in UNIT_TYPES:
            raise TypeError
        else:
            self._unit_type = unit_type.upper()

        # Do some error checking to confirm pins
        if on_off_pin:
            if on_pin or off_pin:
                raise HvacPinError(
                    'Only "on_off_pin" or "on_pin" AND "off_pin" are allowed')
            self._on_pin = on_off_pin
            self._off_pin = on_off_pin
            self._relay_type = 'N'
        elif on_pin and not off_pin or off_pin and not on_pin:
            raise HvacPinError('Both "on_pin" and "off_pin" are required')
        else:
            self._on_pin = on_pin
            self._off_pin = off_pin
            self._relay_type = 'L'

        # Other attributes
        self._time_on = None
        self._time_off = None
        if state in UNIT_STATES:
            self._state = state
        else:
            self._state = 'OFF'
        self._timer = False

    @property
    def on_pin(self):
        return self._on_pin

    @property
    def off_pin(self):
        return self._off_pin

    @property
    def relay_type(self):
        return self._relay_type

    @property
    def time_on(self):
        return self._time_on

    @time_on.setter
    def time_on(self, timestamp):
        print(self.time_on)
        # Get the difference in seconds
        try:
            if self.time_on:
                self._time_on += int(timestamp - self.time_off)
            else:
                self._time_on = int(timestamp - self.time_off)
        except TypeError as e:
            print(e)

    @property
    def time_off(self):
        return self._time_off

    @time_off.setter
    def time_off(self, timestamp):
        self._time_off = timestamp

    @property
    def id(self):
        return self._unit_type

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        if self._state != new_state and new_state in UNIT_STATES:
            if not self._timer:
                self._state = new_state
                # Don't want it to switch on and off continuasly so make a timer
                self._timer = create_timer(
                    5 * 60, self.reset_timer)  # 5 min timer
            else:
                raise HvacUnitError('Timer has not reset')
        else:
            raise HvacUnitError(f'Invalid state {new_state}')

    def reset_timer(self):
        print('reseting timer')
        self._timer = False

    @property
    def as_dict(self):
        return {
            'on_pin': self.on_pin,
            'off_pin': self.off_pin,
            'relay_type': self.relay_type,
            'time_on': self.time_on,
            'id': self.id,
            'state': self.state
        }

    def turn_on(self):
        try:
            self.state = 'ON'
            self.time_off = int(time.time())
            return True
        except HvacUnitError as e:
            print(e)
            return False

    def turn_off(self):
        try:
            self.state = 'OFF'
            self.time_on = int(time.time())
            return True
        except HvacUnitError as e:
            print(e)
            return False


class HVAC(GenericDevice):
    def __init__(self, host, name='generic_hvac', raw_data=None,
                 control_board=None, heat_unit=None, ac_unit=None, vent_unit=None):
        raw_data = raw_data or {
            'name': name, 'description': 'Standard HVAC with heater, ac, and vent'}
        super().__init__(host, name, raw_data)
        # setup socket communication
        self._sock = socketio.Client()
        if not isinstance(heat_unit, HVACUnit) or not isinstance(ac_unit, HVACUnit) or not isinstance(vent_unit, HVACUnit):
            raise HvacUnitError()
        else:
            self._heat_unit = heat_unit
            self._ac_unit = ac_unit
            self._vent_unit = vent_unit
            self._control_board = control_board or telemetrix.Telemetrix()
            if self.sock.sid:
                self._thermostat = Thermostat(sock=self.sock)
            else:
                self._thermostat = Thermostat()
        self._units = {'ac': self.ac, 'heater': self.heater, 'vent': self.vent}

        # setup the board
        self.control_board.set_pin_mode_digital_output(self.heater.on_pin)
        self.control_board.set_pin_mode_digital_output(self.heater.off_pin)
        self.control_board.set_pin_mode_digital_output(self.ac.on_pin)
        self.control_board.set_pin_mode_digital_output(self.ac.off_pin)
        self.control_board.set_pin_mode_digital_output(self.vent.on_pin)
        self.control_board.set_pin_mode_digital_output(self.vent.off_pin)

        # Setup the socket
        self.sock.on('connect', handler=self.connect)
        self.sock.on('disconnect', handler=self.disconnect)
        self.sock.on('get_hvac', handler=self.get_hvac)
        self.sock.on('add_sensor', handler=self.add_sensor)
        self.sock.on('get_current_temp',
                     handler=self.thermostat.get_group_temp)
        self.sock.on('change_desired_temp', handler=self.set_desired_temp)
        self.sock.on('main_page', handler=self.connect)
        self.sock.on('get_sensors', handler=self.send_sensors)
        # Make sure everything is off
        for unit in self.units.values():
            self.turn_off(unit)

        self._timer = False
        self._temp_diff = .25

    @property
    def as_dict(self):
        return {
            'host': self.host,
            'name': self.name,
            'raw': self.raw_data,
            'heater': self.heater.as_dict,
            'ac': self.ac.as_dict,
            'vent': self.vent.as_dict,
            # 'board': self.control_board,
            'thermostat': self.thermostat.as_dict
        }

    @property
    def heater(self):
        return self._heat_unit

    @property
    def ac(self):
        return self._ac_unit

    @property
    def vent(self):
        return self._vent_unit

    @property
    def thermostat(self):
        return self._thermostat

    @property
    def control_board(self):
        return self._control_board

    @property
    def units(self):
        return self._units

    @property
    def sock(self):
        return self._sock

    @property
    def connected_to_sock(self):
        if self.sock.sid:
            return True
        return False

    @property
    def temp_diff(self):
        return self._temp_diff

    @temp_diff.setter
    def temp_diff(self, value):
        if value != self.temp_diff:
            self._temp_diff = value

    def connect_to_socket(self):
        while True:
            if self.sock.connected:
                time.sleep(.001)
                continue
            else:
                try:
                    self.sock.connect(HOST)
                except socketio.exceptions.ConnectionError:
                    pass
            time.sleep(.001)

    def check_for_socket(self):
        while True:
            if self.sock.sid:
                break
            else:
                pass
            time.sleep(.001)

    def connect(self):
        print(f'connected to {HOST} with sid of {self.sock.sid}')
        self.thermostat.sock = self.sock
        d = {
            'house_temp': self.thermostat.get_group_temp(self.thermostat.default_area),
            'desired_temp': self.thermostat.desired_temp,
            'thermostat_state': self.thermostat.state
        }
        return d

    def disconnect(self):
        self.thermostat.sock = None

    def get_hvac(self):
        return self.as_dict

    def add_sensor(self, msg):
        sensor_class = getattr(importlib.import_module(
            'smart_thermo.sensors'), msg[3])
        sensor = sensor_class(msg[0], msg[1], differential=msg[2])
        self.thermostat.add_sensor(sensor, self.control_board)

    def set_desired_temp(self, msg):
        try:
            self.thermostat.desired_temp = int(msg)
            if self.connected_to_sock:
                self.sock.emit('changed_temp', self.thermostat.desired_temp)
                return self.thermostat.desired_temp
        except Exception as e:
            print(f'exception in set_desired_temp:  {e}')

    def send_sensors(self):
        print(f'in send_sensors: {list(self.thermostat.sensors.keys())}')
        try:
            return list(self.thermostat.sensors.keys())
        except Exception as e:
            print(f'could not get sensors: {e}')

    def turn_on(self, unit):
        if not isinstance(unit, HVACUnit):
            raise HvacUnitError(f'{unit} is not the right type')
        try:
            if unit.turn_on():
                self.control_board.digital_write(unit.on_pin, 1)
                print(f'turned on {unit.id}')
                print(f'set pin {unit.on_pin} to 1')
                time.sleep(.1)
                if unit.relay_type == 'L':
                    self.control_board.digital_write(unit.on_pin, 0)
                    print(f'set pin {unit.on_pin} to 0')
                    time.sleep(.1)
        except Exception as e:
            print('in turn_on')
            print(e)

    def turn_off(self, unit):
        if not isinstance(unit, HVACUnit):
            raise HvacUnitError(f'{unit} is not the right type')
        try:
            if unit.turn_off():
                self.control_board.digital_write(unit.off_pin, 1)
                print(f'turned off {unit.id}')
                print(f'set pin {unit.off_pin} to 1')
                time.sleep(.1)
                if unit.relay_type == 'L':
                    self.control_board.digital_write(unit.off_pin, 0)
                    print(f'set pin {unit.off_pin} to 0')
                    time.sleep(.1)
        except Exception as e:
            print('in turn_off')
            print(e)

    def startup(self):
        print('starting up')
        if not self.control_board:
            self.control_board = telemetrix.Telemetrix()
        create_daemon(self.connect_to_socket)
        create_daemon(self.check_for_socket)
        self.setup_sensors()
        # else:
        #     raise BoardConnectError('The board is already running')

    def shutdown(self, quit=True):
        if self.control_board:
            print(f'shutting down {self.control_board}')
            for unit in self.units.values():
                self.turn_off(unit)
            self.control_board.shutdown()
            if quit:
                sys.exit()
        else:
            if quit:
                sys.exit()
            else:
                raise BoardConnectError('no board to shutdown')

    def setup_sensors(self):
        tstat = self.thermostat
        # tstat.add_sensor(LM35('hall', 3), hvac.control_board)
        tstat.add_sensor(LM35('mbed', 4), hvac.control_board)
        tstat.add_sensor(LM35('lroom', 5), hvac.control_board)

    def run(self):
        while True:
            while self.thermostat.state == 'OFF':
                pass
            while self.thermostat.state == 'COOL':
                try:
                    temp = self.thermostat.get_group_temp(
                        self.thermostat.default_area)
                    if self.thermostat.desired_temp:
                        if temp > self.thermostat.desired_temp + self.temp_diff:
                            if self.ac.state != 'ON':
                                try:
                                    self.turn_on(self.ac)
                                except HvacUnitError:
                                    pass
                        elif temp < self.thermostat.desired_temp - self.temp_diff:
                            if self.ac.state != 'OFF':
                                try:
                                    self.turn_off(self.ac)
                                except HvacUnitError:
                                    pass
                except Exception as e:
                    pass
                time.sleep(1)
            while self.thermostat.state == 'HEAT':
                try:
                    temp = self.thermostat.get_group_temp(
                        self.thermostat.default_area)
                    if temp > self.thermostat.desired_temp + self.temp_diff:
                        self.turn_off(self.heater)
                    elif temp < self.thermostat.desired_temp - self.temp_diff:
                        self.turn_on(self.heater)
                except Exception as e:
                    print(e)
                time.sleep(1)
            while self.thermostat.state == 'VENT':
                try:
                    temp = self.thermostat.get_group_temp(
                        self.thermostat.default_area)
                    # TODO: set a timer to turn on and off

                    def switch():
                        if self.vent.state == 'ON':
                            self.turn_off(self.vent)
                        else:
                            if self.thermostat.state == 'VENT':
                                self.turn_on(self.vent)
                    switch()
                    create_timer(15 * 60, switch)

                except Exception as e:
                    print(e)


hvac = HVAC(HOST, control_board=telemetrix.Telemetrix(), heat_unit=HVACUnit('heater', on_pin=4, off_pin=5),
            ac_unit=HVACUnit('airconditioner', on_pin=6, off_pin=7), vent_unit=HVACUnit('vent', on_pin=2, off_pin=3))
hvac.startup()
# create_daemon(hvac.run)
hvac.thermostat.state = 'COOL'
hvac.run()

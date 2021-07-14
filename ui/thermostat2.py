#!/usr/bin/env python

from flask import Flask, render_template, url_for, jsonify, request, redirect
# from flask_mqtt import Mqtt
import json, os, signal
from flask_socketio import SocketIO
import socketio
import eventlet
from pathlib import Path
import sys
import importlib
import time

# BUG: Find another way to do this
#  Should go away when used as package
sys.path.append('/home/jbrodie')

from brodie_house.tools import *
from brodie_house.exceptions import *
from brodie_house.sensors import *
import brodie_house.devices.hvac2 as hvac2

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET'] = 'WhereAmI@Now?'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['THREADING'] = True

# Variables
socketio = SocketIO(app)

HOST = 'http://ziggy.ziggyhome:5000'

SOCKET = socketio.Client()

VENT = hvac2.HVACUnit('VENT', on_pin=2, off_pin=3)
HEATER = hvac2.HVACUnit('HEATER', on_pin=4, off_pin=5)
AC = hvac2.HVACUnit('AIRCONDITIONER', on_pin=6, off_pin=7)
THERMOSTAT = hvac2.Thermostat('MAIN')

##################################################
# Socket Stuff

def connect_sockets():
    try:
        THERMOSTAT.sock = HVAC.sock
    except Exception as e:
        print(f'Cant connect sockets:  {e}')

def disconnect_sockets():
    try:
        THERMOSTAT.sock = None
    except Exception as e:
        print(f'Could not disconnect sockets:  {e}')

def get_thermostat_basics():
    return {
        'house_temp': THERMOSTAT.get_group_temp(THERMOSTAT.default_area),
        'desired_temp': THERMOSTAT.desired_temp,
        'thermostat_state': THERMOSTAT.state
        }
# HVAC.sock.on('connect', handler=connect_sockets())
# HVAC.sock.on('disconnect', handler=disconnect_sockets())
# HVAC.sock.on('main_page', handler=HVAC.setup_main_page)

@socketio.on('connect')
def connect():
    print('connected socketio')
    socketio.emit('main_page_js', get_thermostat_basics())
    # socketio.emit('main_page', callback=setup_main_page)

@socketio.on('disconnect')
def disconnect():
    print('Client disconnected')

# def setup_main_page(msg):
#     socketio.emit('inside_temperature', msg.get('house_temp'))
#     socketio.emit('thermostat_state', msg.get('thermostat_state'))
#     socketio.emit('desired_temp', msg.get('desired_temp'))
#
# def tryme(msg):
#     global hvac
#     hvac = msg
#     # print('in tryme      ', hvac)
#     socketio.emit('thermostat_data', hvac.get('thermostat'))
#     socketio.emit('desired_temp_change', hvac.get('desired_temp'))

# def set_current_temp(temp):
#     socketio.emit('area_temp', temp)

# @socketio.on('get_area_temp')
# def get_area_temp(msg):
#     try:
#         socketio.emit('get_current_temp', msg, callback=set_current_temp)
#     except TypeError:
#         set_current_temp('- -')

# @socketio.on('add_sensor')
# def add_sensor(msg):
#     print(msg)
#     socketio.emit('add_sensor', (msg, ' here am'))
#

# Main Page
# @socketio.on('inside_temp_change')
# def test_message(message):
#     print(f'inside temp changed to {message}')
#     # socketio.emit('inside_temperature', {'data': message['data']})

# @socketio.on('change_desired_temp')
# def change_desired_temp(message):
#     global hvac
#     temp = socketio.emit('change_desired_temp', message)

# @socketio.on('changed_temp')
# def changed_temp(message):
#     socketio.emit('changed_temp', message)

# @socketio.on('change_state')
# def change_state(message):
#     print(f'state changed to {message}')

@app.route('/thermostat/')
def thermostat():
    data = socketio.emit('main_page')
    socketio.emit('main_page_js', data)
    return render_template('thermostat2.html', data=data)

@app.route('/admin_page/', methods = ['POST', 'GET'])
def admin_page():
    global hvac
    if request.method == 'POST':
        form = request.form
        if len(form.keys()) != 4:
            print('error')
        else:
            try:
                # s = getattr(importlib.import_module('brodie_house.sensors'), form.get('sensor_type'))
                # # print(form.get('sensor_name'))
                # print(s)
                # print(type(form.get('control_pins')))
                # print(type(int(form.get('control_pins'))))
                new_sensor = [form.get('sensor_name'), int(form.get('control_pins')), int(form.get('differential')), form.get('sensor_type')]
                print('new_sensor', new_sensor)
                socketio.emit('add_sensor', new_sensor)
                socketio.emit('get_thermostat', callback=tryme)
                time.sleep(.5)
                # hvac.add_sensor(new_sensor)
            except Exception as e:
                print(e)
    # Reload the thermostat

    try:
        avaliable_sensors = list(hvac.get('thermostat').get('sensors'))
        print('avaliable_sensors', avaliable_sensors)
        if avaliable_sensors:
            for s in avaliable_sensors:
                print(hvac.get('thermostat'))
        return render_template('admin.html', sensors = avaliable_sensors)
    except Exception as e:
        return render_template('admin.html', sensors = [])
@app.route('/add_sensor_page/', methods = ['GET', 'POST'])
def add_sensor_page(**kwargs):
    try:
        print(kwargs.get('selected_sensor'), 'in route selected_sensor')
    except:
        pass
    sensors = get_avaliable_sensor_types()
    if request.method == 'POST':
        print('post')
    return render_template('add_sensor.html', selected_sensor=kwargs.get('selected_sensor'), num_of_sensor_types = len(sensors), sensors=sensors)

@app.route('/add_group_page', methods = ['GET', 'POST'])
def add_group_page():
    print(request.method)
    return render_template('add_group.html')

@app.route('/stopServer')
def stopServer():
    os.kill(os.getpid(), signal.SIGINT)
    return jsonify({ "success": True, "message": "Server is shutting down..." })

@app.route('/')
def index():
    return render_template('test.html')#, c_weather = weather.get_current_weather(), f_weather = weather.get_forecast())


def run():
    # asyncio.run(run_thermostat())
    socketio.run(app, host='ziggy.ziggyhome')
    # app.run()

if __name__ == '__main__':
    run()
    # app.run(debug = True)
    # socketio.run(app)

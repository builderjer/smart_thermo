#!/usr/bin/env python

import importlib
import json
import os
import signal
import sys
import time
import eventlet
from pathlib import Path
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_socketio import SocketIO

# BUG: Find another way to do this
#  Should go away when used as package
sys.path.append('/home/jbrodie/Software/oldserver')

from smart_thermo.tools import *
from smart_thermo.exceptions import *

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET'] = 'WhereAmI@Now?'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['THREADING'] = True

socketio = SocketIO(app)

# Variables
hvac = None

##################################################
# Socket Stuff


@socketio.event
def connect():
    global hvac
    # print(hvac, '##########################')
    print('connected socketio')
    socketio.emit('main_page', callback=setup_main_page)


def setup_main_page(msg):
    socketio.emit('inside_temperature', msg.get('house_temp'))
    socketio.emit('thermostat_state', msg.get('thermostat_state'))
    socketio.emit('desired_temp', msg.get('desired_temp'))


def tryme(msg):
    global hvac
    hvac = msg
    socketio.emit('thermostat_data', hvac.get('thermostat'))
    socketio.emit('desired_temp_change', hvac.get('desired_temp'))


def set_current_temp(temp):
    socketio.emit('area_temp', temp)


@socketio.on('get_area_temp')
def get_area_temp(msg):
    try:
        socketio.emit('get_current_temp', msg, callback=set_current_temp)
    except TypeError:
        set_current_temp('- -')


@socketio.on('add_sensor')
def add_sensor(msg):
    print(msg)
    socketio.emit('add_sensor', (msg, ' here am'))


@socketio.on('disconnect')
def disconnect():
    print('Client disconnected')

# Main Page


@socketio.on('inside_temp_change')
def test_message(message):
    socketio.emit('inside_temperature', message)
    # socketio.emit('inside_temperature', {'data': message['data']})


@socketio.on('change_desired_temp')
def change_desired_temp(message):
    global hvac
    temp = socketio.emit('change_desired_temp', message)
    # print(f'changing_desired_temp {temp}, {message}')
    # print(f'desired temp changed to {message}')
    # print(hvac.get('thermostat').get('desired_temp'))


@socketio.on('changed_temp')
def changed_temp(message):
    socketio.emit('changed_temp', message)


@socketio.on('change_state')
def change_state(message):
    print(f'state changed to {message}')
    # try:
    #     hvac.state = message.upper()
    #     socketio.emit('change_thermostat_state', message.upper())
    # except Exception as e:
    #     print(e)


@app.route('/thermostat/')
def thermostat():
    # global hvac
    return render_template('thermostat.html')


@app.route('/admin_page/', methods=['POST', 'GET'])
def admin_page():
    global hvac
    avaliable_sensors = []
    def set_sensors(sensors):
        print(sensors)
        for s in sensors:
            print(f'sensor: {s}')
            avaliable_sensors.append(s)
    if request.method == 'POST':
        form = request.form
        if len(form.keys()) != 4:
            print('error')
        else:
            try:
                # s = getattr(importlib.import_module('smart_thermo.sensors'), form.get('sensor_type'))
                # # print(form.get('sensor_name'))
                # print(s)
                # print(type(form.get('control_pins')))
                # print(type(int(form.get('control_pins'))))
                new_sensor = [form.get('sensor_name'), int(form.get('control_pins')), int(
                    form.get('differential')), form.get('sensor_type')]
                print('new_sensor', new_sensor)
                socketio.emit('add_sensor', new_sensor)
                socketio.emit('get_thermostat', callback=tryme)
                time.sleep(.5)
                # hvac.add_sensor(new_sensor)
            except Exception as e:
                print(e)
    # Reload the thermostat

    try:
        socketio.emit('get_sensors', callback = set_sensors)
        # avaliable_sensors = list(hvac.get('thermostat').get('sensors'))
        print(f'avaliable_sensors: {avaliable_sensors}')

        if avaliable_sensors:
            for s in avaliable_sensors:
                print(s)
        return render_template('admin.html', sensors=avaliable_sensors)
    except Exception as e:
        return render_template('admin.html', sensors=[])


@app.route('/add_sensor_page/', methods=['GET', 'POST'])
def add_sensor_page(**kwargs):
    try:
        print(kwargs.get('selected_sensor'), 'in route selected_sensor')
    except:
        pass
    sensors = get_avaliable_sensor_types()
    if request.method == 'POST':
        print('post')
    return render_template('add_sensor.html', selected_sensor=kwargs.get('selected_sensor'), num_of_sensor_types=len(sensors), sensors=sensors)


@app.route('/add_group_page', methods=['GET', 'POST'])
def add_group_page():
    print(request.method)
    return render_template('add_group.html')


@app.route('/stopServer')
def stopServer():
    os.kill(os.getpid(), signal.SIGINT)
    return jsonify({"success": True, "message": "Server is shutting down..."})


@app.route('/')
def index():
    # , c_weather = weather.get_current_weather(), f_weather = weather.get_forecast())
    return render_template('test.html')


def run():
    # asyncio.run(run_thermostat())
    socketio.run(app, host='192.168.0.241')
    # socketio.run(app, host='ziggy.ziggyhome')
    # app.run()


if __name__ == '__main__':
    run()
    # app.run(debug = True)
    # socketio.run(app)

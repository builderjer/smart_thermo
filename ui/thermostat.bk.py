#!/usr/bin/env python

from flask import Flask, render_template, url_for, jsonify, request, redirect
from flask_mqtt import Mqtt
import json, os, signal
from flask_socketio import SocketIO
import eventlet
from pathlib import Path
import sys
import asyncio
import importlib
import time

# BUG: Find another way to do this
#  Should go away when used as package
sys.path.append('/home/jbrodie')

from brodie_house.devices.thermostat import Thermostat
import brodie_house.sensors as sensors
from brodie_house.weather.weatherapi import Weather
from brodie_house.tools import *
from brodie_house.exceptions import *

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET'] = 'abcdefg'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['THREADING'] = True

app.config['MQTT_BROKER_URL'] = 'ziggyserver.ziggyhome'  # use the free broker from HIVEMQ
app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
# app.config['MQTT_USERNAME'] = 'ziggy'  # set the username here if you need authentication for the broker
# app.config['MQTT_PASSWORD'] = 'ziggy'  # set the password here if the broker demands authentication
app.config['MQTT_KEEPALIVE'] = 5  # set the time interval for sending a ping to the broker to 5 seconds
app.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes
mqtt = Mqtt(app)
socketio = SocketIO(app)


# Variables
t_stat = Thermostat('main', autostart=False)

# weather = Weather()

@socketio.on('inside_temp_change')
def test_message(message):
    socketio.emit('inside_temperature', {'data': message['data']})

@socketio.on('change_desired_temp')
def change_desired_temp(message):
    print(message, type(message))
    # print(t_stat.desired_temp)
    try:
        t_stat.desired_temp = message

    except(TempError) as e:
        print(e)
    # print(t_stat.desired_temp)
    socketio.emit('desired_temp_change', t_stat.desired_temp)
    # mqtt.publish('ziggy/climate/thermostat/desired_temp', message)

@socketio.on('change_state')
def change_mode(message):
    try:
        t_stat.state = message.upper()
        socketio.emit('change_thermostat_state', message.upper())
    except Exception as e:
        print(e)

###################################
#  Weather
###################################
# @socketio.on('update_weather')
# def update_weather(data):
#     print('in update_weather')
#     # current_weather = weather.get_current_weather()
#     # current_forecast = weather.get_forecast().get('day_1')
# #     # print('updating weather', current_weather)
#     socketio.emit('forecast_high_temperature', weather.forecast.get('maxTempF'))
#     socketio.emit('forecast_low_temperature', weather.forecast.get('minTempF'))
#     socketio.emit('forecast_summary', weather.forecast.get('weather'))
#     forecast_icon = url_for('static', filename = 'images/weather/AerisIcons/{}'.format(weather.forecast.get('icon')))
#     socketio.emit('forecast_icon', forecast_icon)
# #     print('before emit')
#     socketio.emit('current_outside_temperature', round(weather.current.get('tempF')))
# #     print('after emit')
# #     current_icon = current_weather.get('icon')
# #     print('currnet icon:  ', current_icon)
#     icon = url_for('static', filename = 'images/weather/AerisIcons/{}'.format(weather.current.get('icon')))
# #     print('icon:  ', icon)
#     socketio.emit('current_weather_icon', icon)
###################################
@socketio.on('connect')
def connect():
    print('connected socketio')
    socketio.emit('change_thermostat_state', t_stat.state)
    socketio.emit('desired_temp_change', t_stat.desired_temp)

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    print('connected !!')
    mqtt.subscribe('ziggy/climate/thermostat/#')
    # mqtt.subscribe('home/mytopic')

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data =dict(
        topic = message.topic,
        payload = message.payload.decode()
    )
    print(data)
    if data['topic'].endswith('temperature'):
        socketio.emit('inside_temperature', data=data['payload'])
    # socketio.emit('test', data=data)

@app.route('/thermostat/')
def thermostat():
    return render_template('thermostat.html')

@app.route('/admin_page/', methods = ['POST', 'GET'])
def admin_page():
    if request.method == 'POST':
        form = request.form
        if len(form.keys()) != 4:
            print('error')
        else:
            try:
                s = getattr(importlib.import_module('brodie_house.sensors'), form.get('sensor_type'))
                # print(form.get('sensor_name'))
                new_sensor = s(form.get('sensor_name'), int(form.get('control_pins')), differential=int(form.get('differential')))
                # print('new_sensor', new_sensor)
                t_stat.add_sensor(new_sensor)
            except Exception as e:
                print(e)
    avaliable_sensors = t_stat.sensors
    return render_template('admin.html', sensors=avaliable_sensors)

@socketio.on('change_sensor_value')
def change_sensor_value(message):
    print('sensor', message)
    add_sensor_page(selected_sensor=message)

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
    return render_template('add_group.html', avaliable_sensors=t_stat.sensors)

@app.route('/stopServer')
def stopServer():
    os.kill(os.getpid(), signal.SIGINT)
    return jsonify({ "success": True, "message": "Server is shutting down..." })

@app.route('/')
def index():
    return render_template('test.html', desired_temp = t_stat.desired_temp)#, c_weather = weather.get_current_weather(), f_weather = weather.get_forecast())

def run():
    socketio.run(app, host='ziggyweb.ziggyhome')
    # app.run()

@socketio.on('update_temps')
def update_temps():
    print('updating temps')
    temps = []
    print(t_stat.sensors)
    try:
        for s in t_stat.sensors:
            print(s, 'in try')
            temps.append(t_stat.get_sensor_temp(s))
    except Exception as e:
        print(e)
    print(temps)
    socketio.emit('sensor_temps', temps)

if __name__ == '__main__':
    run()
    # app.run(debug = True)
    # socketio.run(app)

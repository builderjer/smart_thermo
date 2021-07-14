#!/usr/bin/env python

from flask import Flask, render_template, url_for, jsonify, request, redirect
import json, os, signal
from flask_socketio import SocketIO
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

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET'] = 'abcdefg'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['THREADING'] = True

socketio = SocketIO(app)

# Variables
t_stat = None

@socketio.on('connect')
def connect():
    print('connected socketio')
    socketio.emit('get_thermostat', callback=tryme)
    try:
        socketio.emit('get_current_temp', data=t_stat.get(default_area), callback=current_temp)
    except AttributeError:
        pass
    except NameError:
        pass

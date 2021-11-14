#!/bin/sh

. /home/pi/smart_thermo/.venv/bin/activate
cd /home/pi/smart_thermo
python -m start.py &
python -c 'from devices.hvac import hvac'

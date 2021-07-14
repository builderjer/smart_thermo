import paho.mqtt.client as mqtt
import logging
import inspect
import sys
import os
import importlib

from threading import Thread
from threading import Timer

sys.path.append('/home/jbrodie')

def merge_dict(base, delta):
    """
        Recursively merging configuration dictionaries.

        Args:
            base:  Target for merge
            delta: Dictionary to merge into base
    """

    for k, dv in delta.items():
        bv = base.get(k)
        if isinstance(dv, dict) and isinstance(bv, dict):
            merge_dict(bv, dv)
        elif isinstance(dv, list) and isinstance(bv, list):
            for v in dv:
                if v not in bv:
                    bv.append(v)
        else:
            base[k] = dv
    return base


def create_daemon(func):
    t = Thread(target=func)
    t.setDaemon(True)
    t.start()
    return t

def create_timer(delay, func, *args, **kwargs):
    t = Timer(delay, func, args, kwargs)
    t.start()
    return t

def convert_temp(temp, output_format):
    if output_format == 'F':
        return ((temp / 5) * 9) + 32
    elif output_format == 'C':
        return ((temp - 32) * 5) / 9
    raise TypeError(f'{output_format} is not a valid conversion type')

def get_avaliable_sensor_types():
    from brodie_house import sensors
    c = [cls_name for cls_name, cls_obj in inspect.getmembers(sys.modules['brodie_house.sensors']) if inspect.isclass(cls_obj)]
    s = []
    # while True:
    for cl in c:
        if cl.endswith('Error') or cl.endswith('Sensor'):
            continue
        else:
            print(type(cl))
            s.append(cl)
            # c.pop(c.index(cl))
        print(s)
    return s

class MQTTClient():
    """ A class to connect to a MQTT broker

    DO NOT inherit this class, instead use it as an attribute in the MQTTObject class
    """

    def __init__(self, name=None, host=None, port=None, keepalive=None, bind_address=None):
        self.LOGGER = logging.getLogger("__main__.tools.MQTTClient")
        self._name = name or 'generic_mqtt_client'
        self._host = host or 'localhost'
        self._port = port or 1883
        self._keepalive = keepalive or 60
        self._bind_address = bind_address or ''
        self._client = mqtt.Client(self.name)
        self._client.on_connect = self.on_connect
        self._client.on_disconnect = self.on_disconnect
        self._client.on_message = self.on_message
        self._client.on_publish = self.on_publish

        self._enabled = False

        # self.desiredTemp = None
        # self.client.on_connect = self.onConnect
        # self.client.connect(host, port, keepalive, bind_address)
        # self.client.loop_start()
        # time.sleep(1)

    @property
    def name(self):
        return self._name

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def keepalive(self):
        return self._keepalive

    @property
    def bind_address(self):
        return self._bind_address

    @property
    def client(self):
        return self._client

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value

    def connect(self, **kwds):
        for k, v in kwds.items():
            if k == "host":
                self._host = v
            if k == "port":
                self._port = v
            if k == "keepalive":
                self._keepalive = v
            if k == "bind_address":
                self._bind_address = bind_address

        try:
            self.client.connect(self.host, self.port, self.keepalive, self.bind_address)
            return True
        except Exception as e:
            self.LOGGER.error("Cannot connect to mqtt broker. {}".format(e))
            return False

    def on_connect(self, client, userdata, flags, rc):
        # self.client.subscribe("ziggy/climate/temp/desired")
        if rc == 0:
            self.enabled = True

    def on_disconnect(self):
        self.enabled = False

    def on_message(self, client, userdata, msg):
        """ Override this function """
        pass
        # message = {}
        # if msg.topic == "ziggy/climate/temp/desired":
        #     message = str(msg.payload.decode())
        #     self.LOGGER.debug(message)
        #     self.desiredTemp = int(message)

    def on_publish(self):
        """ Override this function """
        pass

    def start(self):
        self.client.loop_start()
        time.sleep(1)

    def stop(self):
        self.client.loop_stop()
        time.sleep(1)

    # def publish(self, topic, message, qos=1, retain=True):
    #     if self.enabled:
    #         self.client.publish(topic, message, qos, retain)
    #     else:
    #         self.LOGGER.error("MQTT server not connected at {} port {}".format(self.host, self.port))

class MQTTObject():
    """ A parent class for anything that needs to recieve or publish messages
    from a MQTT broker """
    def __init__(self, broker: MQTTClient):
        if not isinstance(broker, MQTTClient):
        # if type(broker) != MQTTClient:
            raise TypeError("broker must be of type MQTTClient")
        self._client = broker
        self._messages = {}
        self._on_message = self.client.on_message

    @property
    def client(self):
        return self._client

    @property
    def messages(self):
        return self._messages


    def on_message(self, client, userdata, msg):
        """ Override me """
        pass

    def subscribe(self, topic):
        try:
            self.client.subscribe(topic)
            return True
        except Exception as e:
            LOGGER.error("Could not subscribe to {}  {}".format(topic, e))
            return False

    def publish(self, topic, message, qos=1, retain=True):
        """ Can be overridden """
        try:
            self.client.publish(topic, message, qos, retain)
            return True
        except Exception as e:
            LOGGER.error("Could not publish to topic {}  {}".format(topic, e))
            return False

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

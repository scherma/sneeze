#!/usr/bin/env python

import time
from watchdog.observers import Observer
import re
import os
from hayfever import HayFever
import configure
import sys

def Sneeze(dest=""):
    # if user supplies a destination as an argument, use that
    configuration = configure.Configure(dest)
    # create event handler
    # dictionary contains mapping of interface to path and pattern
    # HayFever must verify which path and pattern an event matches
    # and include the relevant interface in the event
    event_handler = HayFever(**configuration.confdata)
    
    threads = []
    observer = Observer()

    for interface, values in configuration.confdata['watch'].items():
        # create event detector
        observer.schedule(event_handler, values['path'], recursive=True)
        threads.append(observer)
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


#!/usr/local/bin/python

import time
from watchdog.observers import Observer
import os
from hayfever import HayFever
			

if __name__ == "__main__":
	d = {}
	with open("sneeze.conf") as f:
    		for line in f:
       			(key, val) = line.strip().split(": ")
			d[key] = val
	if not os.path.isdir(d['watch']):
		raise ValueError("{} is not a valid directory.".format(d['watch']))
	if len(d['destination']) < 1:
		raise ValueError("Destination must be provided.")


	# create event handler
    	event_handler = HayFever(**d)
	# create event detector
    	observer = Observer()
    	observer.schedule(event_handler, d['watch'], recursive=True)
    	observer.start()
    	try:
        	while True:
            		time.sleep(1)
    	except KeyboardInterrupt:
        	observer.stop()
	observer.join()

#!/usr/bin/env python

import time
from watchdog.observers import Observer
import os
from hayfever import HayFever
			

if __name__ == "__main__":
	d = {}
	d['watch'] = []
	with open("sneeze.conf") as f:
    		for line in f:
       			(key, val) = line.strip().split(": ")
			if key == "watch":
				d['watch'].append(val)
			else:
				d[key] = val
	for p in d['watch']:
		if not os.path.isdir(p):
			raise ValueError("{} is not a valid directory.".format(p))

	if len(d['destination']) < 1:
		raise ValueError("Destination must be provided.")

	# create event handler
	event_handler = HayFever(thiswatch=p, **d)

	for p in d['watch']:
		# create event detector
		observer = Observer()
		observer.schedule(event_handler, p, recursive=True)
	    	observer.start()
		try:
			while True:
				time.sleep(1)
		except KeyboardInterrupt:
			observer.stop()
		observer.join()

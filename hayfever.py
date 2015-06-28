#!/usr/bin/env python
from watchdog.events import FileSystemEventHandler
import unified2.parser
import re
import json
import requests
import struct
import base64
import socket
import os.path
import time

class HayFever(FileSystemEventHandler):

    	def __init__(self, *args, **kwargs):
        	super(HayFever, self).__init__()
        	try:
			self.lasteventfile = kwargs.pop('lasteventfile')
			self.send_to = kwargs.pop('destination')
			self.useragent = kwargs.pop('useragent')
			self.watchpath = kwargs.pop('watch')
			if 'verifycerts' in kwargs and kwargs.pop('verifycerts') == 'False': self.verify=False 
			else: self.verify=True
		except KeyError as e:
			print "You have not defined '{}' properly in the config file!".format(e.args[0])
			exit()
		self.on_start()



	def _interface(self):
		# snort names log directory with the interface name
		pathdirs = self.watchpath.split('/')
		return pathdirs[(len(pathdirs) - 1)].split('_')[1]



	def _lastevent(self):
		ev_id = 0
		ev_time = 0
		with open(self.lasteventfile, 'a+') as lastevent:
			lastevent.seek(0)
			line = lastevent.readline()
			try:
				# If the file has data, store it in the variables
				# If it doesn't, variables will default to nil and and all
				# events will be treated as new
				(ev_id, ev_time,) = line.strip().split(':')
			except:
				do_nothing = 1
			return {'event_id': ev_id,
				'event_time': ev_time}



	def build_data_to_send(self, event = object, allfiles = False):
		# Let's make this RESTy; every time we send something, identify
		# the origin sensor as part of the data
		events = {}
		events['events'] = {}
		events['sensor'] = socket.gethostname()
		events['interface'] = self._interface()
		if allfiles:
			events['events'].update(self.find_all_new_events())
		else:
			events['events'].update(self.find_new_events_in_file(event.src_path, self._lastevent()))
		return events



	def find_new_events_in_file(self, eventfile, lastevent):
		events = {}
		# First make sure the file that changed is unified2
		if re.search('\\.u2\\.\\d+$', eventfile):
			# Check every event in the file
			for (ev, ev_tail,) in unified2.parser.parse(eventfile):
				# If it's a new event, add it to the dict
				if int(ev['event_id']) > int(lastevent['event_id']):
					b64tail = base64.b64encode(ev_tail)
					events[ev['event_id']] = [ev, b64tail]

		return events



	def find_all_new_events(self):
		lastevent = self._lastevent()
		events = {}
		# Iterate through every file in the directory to identify new events
		for f in [ os.path.join(self.watchpath, fn) for fn in next(os.walk(self.watchpath))[2] ]:
			# Event won't be new unless the file was modified after the last event sent
			# Also ensure the file is a unified2 file
			if ( float(lastevent['event_time']) < os.path.getmtime(f) and
				re.search('\\.u2\\.\\d+$', f) ):
				# Add anything new to the dictionary
				events.update(self.find_new_events_in_file(f, lastevent))

		return events



	def send_data(self, eventdata):
		success = ""
		tries = 0
		r = None
		# If at first you don't succeed, try again. And again, and again, and again, and again.
		# Server must return "{'Success': 1}" in the text or we will assume the delivery failed.
		while not (success == "200" and tries <= 5):
			headers = {'User-Agent': self.useragent,
			'Content-Type': 'application/json'}
			url = self.send_to
			r = requests.put(url, headers=headers, data=json.dumps(eventdata), verify=self.verify)
			success = r.status
			if r.status == "200":
				# Store the highest delivered event ID in the lastevent file
				with open(self.lasteventfile, 'w') as lastev:
					maxid = max([ int(k) for k in eventdata['events'].keys() ])
					lastev.write('{0}:{1}'.format(str(maxid), str(time.time())))
			tries += 1
		
		# If we fail at delivering the data, complain.
		if not success == "200":
			alert = 'Alert: {} attempts to send event data failed'.format(str(tries))
			r = requests.put(self.send_to, headers={'User-Agent': self.useragent,
				'Content-Type': 'text/plain'}, data=alert, verify=self.verify)



	def on_created(self, event):
		if re.search('\\.u2\\.\\d+$', event.src_path):
			events = self.build_data_to_send(event)
			if len(events['events']) > 0:
				self.send_data(events)



	def on_modified(self, event):
		if re.search('\\.u2\\.\\d+$', event.src_path):
			events = self.build_data_to_send(event)
			if len(events['events']) > 0:
				self.send_data(events)



	def on_start(self):
		events = self.build_data_to_send(allfiles=True)
		if len(events['events']) > 0:
			self.send_data(events)

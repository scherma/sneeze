#!/usr/bin/env python
from watchdog.events import RegexMatchingEventHandler
import unified2.parser
import re
import json
import requests
import struct
import base64
import socket
import os.path
import time
import sqlite3

class HayFever(RegexMatchingEventHandler):

    	def __init__(self, *args, **kwargs):
        	super(HayFever, self).__init__()
        	try:
			self.lasteventfile = kwargs.pop('lasteventfile')
			self.send_to = kwargs.pop('destination')
			self.useragent = kwargs.pop('useragent')
			if 'verifycerts' in kwargs and kwargs.pop('verifycerts') == 'false': self.verify=False 
			else: self.verify=True
			self.watch = kwargs.pop('watch')
			self.on_start()
		except KeyError as e:
			print "You have not defined '{}' properly in the config file!".format(e.args[0])
			exit()

	def _interface_for_event(self, event):
		# for a given file created/modified event, get the interface it relates to
		# will always return the first match - users must define path and pattern
		# well for this to work properly
		for key, values in self.watch.items():
			if event.src_path.startswith(values['path']):
				# if there is a pattern, test that the event file matches it
				# if both match, this is the interface to give
			 	if 'pattern' in values.keys():
					if re.match(values['pattern'], event.src_path):
						return key
				# if there is no pattern but the paths match, this is the right interface
				else:
					return key



	def build_data_to_send(self, interface = '', event = object, allfiles = False, path = str):
		# Let's make this RESTy; every time we send something, identify
		# the origin sensor as part of the data
		events = {}
		events['sensor'] = socket.gethostname()
		events['eventdata'] = {}
		for interface, values in self.watch.items():
			events_for_interface = {interface: {}}
			if allfiles:
				events_for_interface[interface].update(self.find_all_new_events(values['path']))
			else:
				events_for_interface[interface].update(self.find_new_events_in_file(event.src_path, self.get_last_event(path)))
			if len(events_for_interface[interface].keys()) > 0:
				events['eventdata'].update(events_for_interface)
		return events

	def last_event_for_interface(self, interface): #changeme
		a = 1




	def find_new_events_in_file(self, eventfile, lastevent):
		events = {}
		# First make sure the file that changed is unified2
		if re.search('\\.u2\\.\\d+$', eventfile):
			# Check every event in the file
			for (ev, ev_tail,) in unified2.parser.parse(eventfile):
				# If it's a new event, add it to the dict
				if int(ev['event_id']) > int(lastevent['event_id']):
					if "packet_data" in ev:
						ev['packet_data'] = base64.b64encode(ev['packet_data'])
					b64tail = base64.b64encode(ev_tail)
					events[ev['event_id']] = [ev, b64tail]

		return events



	def find_all_new_events(self, path):
		lastevent = self.get_last_event(path)
		events = {}
		# Iterate through every file in the directory to identify new events
		for f in [ os.path.join(path, fn) for fn in next(os.walk(path))[2] ]:
			# Event won't be new unless the file was modified after the last event sent
			# Also ensure the file is a unified2 file
			if len(lastevent) > 0 and( float(lastevent['event_time']) < os.path.getmtime(f) and
				re.search('\\.u2\\.\\d+$', f) ):
				# Add anything new to the dictionary
				events.update(self.find_new_events_in_file(f, lastevent))

		return events
	
	

	def write_last_event(self, events):
		# Store the highest delivered event ID in the lastevent file
		with sqlite3.connect('trace.db') as lastev:
			c = lastev.cursor()
			for interface, values in events['eventdata'].iteritems():
				maxid = max([ int(k) for k in values.keys() ])
				sqlstr = "INSERT OR REPLACE INTO lastevent (event_id, event_time, transmit_time, interface) VALUES (?, ?, ?, ?)"
				c.execute(sqlstr,[maxid,values[maxid][0]["packet_second"],time.time(),interface])	#changeme
				lastev.commit()

	def get_last_event(self, path):
		thisinterface = ""
		for interface, details in self.watch.iteritems():
			if details['path'] == path:
				thisinterface = interface
		
		with sqlite3.connect('trace.db') as lastevent:
			c = lastevent.cursor()
			c.execute("SELECT interface,event_id,event_time,transmit_time FROM lastevent WHERE interface = ?", [thisinterface])
			rows = c.fetchone()
			columns = ("interface", "event_id", "event_time", "transmit_time")
			result = {} 
			for i in range(len(columns)):
				result[columns[i]] = i
			return result

#	def debug_data(self,data,depth):
#		indent = ''
#		for x in range(0,depth):
#			indent += '\t'
#		if isinstance(data,dict):
#			for key,value in data.iteritems():
#				print "{}{}: {}\n".format(indent, type(key), str(key))
#				print json.dumps(key)
#				self.debug_data(value, depth + 1)
#		elif isinstance(data,list):
#			for value in data:
#				self.debug_data(value, depth + 1)
#		else:
#			print "{}{}: {}\n".format(indent, type(data), str(data))
#			print json.dumps(data)

	def send_data(self, eventdata):
		success = ""
		tries = 0
		r = None
		# If at first you don't succeed, try again. And again, and again, and again, and again.
		# Server must return 200 OK or we will assume the delivery failed.
		while tries <= 5:
			headers = {'User-Agent': self.useragent,
			'Content-Type': 'application/json'}
			url = self.send_to
			r = requests.put(url, headers=headers, data=json.dumps(eventdata), verify=self.verify)
			success = r.status_code
			if r.status_code == "200":
					break
					success = r.status_code
			tries += 1
		
		
		# If we fail at delivering the data, complain.
		if not success == 200:
			alert = 'Alert: {} attempts to send event data failed'.format(str(tries))
			r = requests.put(self.send_to, headers={'User-Agent': self.useragent,
				'Content-Type': 'text/plain'}, data=alert, verify=self.verify)
		else:
			self.write_last_event(eventdata)



	def on_created(self, event):
		ev_interface = self._interface_for_event(event)
		if ev_interface:
			events = self.build_data_to_send(interface=ev_interface, event=event)
			if ev_interface in events.keys() and len(events[ev_interface]) > 0:
				self.send_data(events)



	def on_modified(self, event):
		ev_interface = self._interface_for_event(event)
		if ev_interface:
			events = self.build_data_to_send(interface=ev_interface, event=event)
		if ev_interface in events.keys() and len(events[ev_interface]) > 0:
			self.send_data(events)



	def on_start(self):
		events = self.build_data_to_send(allfiles=True)
		if len(events['eventdata']) > 0:
			self.send_data(events)

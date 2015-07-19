#!/usr/bin/env python
import sqlite3
import os
import re

class Configure():
	def __init__(self):
		d = {}
		d['watch'] = {}
		with open("sneeze.conf") as f:
			interface = ''
			for line in f:
				values = self.get_conf_item(line)
				if 'interface' in values.keys():
					d['watch'][values['interface']] = {}
					interface = values['interface']
				elif 'path' in values.keys():
					d['watch'][interface]['path'] = values['path']
				elif 'pattern' in values.keys():
					d['watch'][interface]['pattern'] = values['pattern']
				else:
					d.update(values)
		for interface, values in d['watch'].items():
			if not os.path.isdir(values['path']):
				raise ValueError("{} is not a valid directory.".format(values['path']))

		if len(d['destination']) < 1:
			raise ValueError("Destination must be provided.")

		self.confdata = d
		
		if not os.path.exists('trace.db'):
			self.create_tracefile()


	def get_conf_item(self, line):
		groups = re.match(r'^(?P<key>[a-z]+)\:\s(?P<val>.*)[\r\n]?', line)
		if groups.group('key') and groups.group('val'):
			return { groups.group('key'): groups.group('val') }
		else:
			raise ValueError("{} is not a valid configuration option".format(line))

	def create_tracefile(self):
		conn = sqlite3.connect('trace.db')
		c = conn.cursor()

		c.execute('''CREATE TABLE lastevent
				(interface text, event_id int, event_time int, transmit_time int)''')

		conn.commit()
		conn.close()

#!/usr/bin/env python
from watchdog.events import RegexMatchingEventHandler
import unified2.parser, re, json, requests, base64, socket
import os.path, time, sqlite3, sys, spooler, threading
from requests import ConnectionError

class HayFever(RegexMatchingEventHandler):
    def __init__(self, *args, **kwargs):
        super(HayFever, self).__init__()
        try:
            self.lasteventfile = kwargs.pop('lastevent')
            self.send_to = kwargs.pop('destination')
            self.useragent = kwargs.pop('useragent')
            if 'verifycerts' in kwargs and kwargs.pop('verifycerts') == 'false': self.verify=False 
            else: self.verify=True
            self.watch = kwargs.pop('watch')
            self.retry_time = kwargs.pop('retry_time')
            self.timer = threading.Timer(self.retry_time, self.unwind_spool)
        except KeyError as e:
            print >> sys.stderr, "You have not defined '{}' properly in the config file!".format(e.args[0])
            exit()
        self.unwind_spool()
        self.on_start()

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
                # if there is no pattern but the paths match, return the key
                else:
                    return key



    def build_data_to_send(self, interface = '', event = object, allfiles = False, path = str):
        # every time we send something, identify the origin sensor as part of the data
        events = {}
        events['sensor'] = socket.gethostname()
        events['eventdata'] = {}
        # always prep data with the same structure, even if there only events from a single interface
        for interface, values in self.watch.items():
            events_for_interface = {interface: {}}
            # check entire directory for new events when script starts
            # otherwise just check the file which got updated
            if allfiles:
                events_for_interface[interface].update(self.find_all_new_events(values['path']))
            # only add events into the section for that snort instance
            elif event.src_path.startswith(values['path']):
                events_for_interface[interface].update(self.find_new_events_in_file(event.src_path, self.get_last_event(path)))
            if len(events_for_interface[interface].keys()) > 0:
                events['eventdata'].update(events_for_interface)
        return events



    def last_event_for_interface(self, interface): #changeme
        with sqlite3.connect(self.lasteventfile) as ledb:
            c = ledb.cursor()
            c.execute('SELECT interface,event_id,event_time,event_micro_time,transmit_time FROM lastevent WHERE interface = ?', interface)
            data = c.fetchone()
            event = {}
            event["interface"] = interface
            event["event_id"] = data[1]
            event["event_time"] = data[2]
            event["event_micro_time"] = data[3]
            event["transmit_time"] = data[4]

            return event

    def build_events_into_dict(self, events, ev, ev_tail):
        # events have an entry defining the signature, revision etc
        # but may have an additional entry containing packet data
        # therefore only create a new list if the event is not already
        # found in the dict we are building
        if ev['event_id'] not in events:
            events[ev['event_id']] = []
        if ev_tail:
            b64tail = base64.b64encode(ev_tail)
            events[ev['event_id']].append((ev,b64tail))
        else:
            events[ev['event_id']].append(ev)



    def find_new_events_in_file(self, eventfile, lastevent):
        events = {}
        # Check every event in the file
        if not os.path.isdir(eventfile):
            for (ev, ev_tail,) in unified2.parser.parse(eventfile):
                # If it's a new event, add it to the dict
                # Need to split this out, otherwise traffic that causes multiple
                # events will result in duplicate transmissions of all but the
                # first event in a group
                if ( int(ev['event_second']) == int(lastevent['event_time'])): 
                    if int(ev['event_id']) > int(lastevent['event_id']):
                        self.build_events_into_dict(events, ev, ev_tail)
                elif int(ev['event_second']) > int(lastevent['event_time']):
                    self.build_events_into_dict(events, ev, ev_tail)
        return events



    def find_all_new_events(self, path):
        lastevent = self.get_last_event(path)
        events = {}
        # Iterate through every file in the directory to identify new events
        for f in [ os.path.join(path, fn) for fn in next(os.walk(path))[2] ]:
            # Event won't be new unless the file was modified after the last event sent
            if float(lastevent['transmit_time']) < os.path.getmtime(f):
            # removed this line as uinifed2 files don't have to follow this naming convention
            # a non unified2 file will not cause an exception, the result will simply be empty
            #    re.search('\\.u2\\.\\d+$', f)):
                # Add anything new to the dictionary
                events.update(self.find_new_events_in_file(f, lastevent))
        return events
    
    

    def write_last_event(self, events):
        # Store the highest delivered event ID in the last event db file
        for interface, values in events['eventdata'].iteritems():
            with sqlite3.connect(self.lasteventfile) as lastev:
                c = lastev.cursor()
                # update DB file with each interface's most recent event
                lastevsql = "SELECT event_id,event_time FROM lastevent WHERE interface = ?"
                c.execute(lastevsql, [interface])
                rows = c.fetchone()
                maxid = max([ int(k) for k in values ])
                if (values[maxid][0]["event_second"] > rows[1] or
                    (values[maxid][0]["event_second"] == rows[1] and
                    maxid > rows[0] )):
                    # only insert/replace if the event is newer - 
                    sqlstr = "INSERT OR REPLACE INTO lastevent (event_id, event_time, event_micro_time, transmit_time, interface) VALUES (?, ?, ?, ?, ?)"
                    insertvals = [maxid, values[maxid][0]["event_second"], values[maxid][0]["event_microsecond"], time.time(), interface]
                    c.execute(sqlstr,insertvals)
                    lastev.commit()



    def get_last_event(self, path):
        # given a watch path, find the most recently sent event
        thisinterface = ""
        for interface, details in self.watch.iteritems():
            if path.startswith(details["path"]):
                thisinterface = interface
        with sqlite3.connect(self.lasteventfile) as lastevent:
            c = lastevent.cursor()
            c.execute("SELECT interface,event_id,event_time,event_micro_time,transmit_time FROM lastevent WHERE interface = ?", [thisinterface])
            rows = c.fetchone()
            columns = ("interface", "event_id", "event_time", "event_micro_time", "transmit_time")
            result = {} 
            
            for i in range(len(columns)):
                if rows:
                    result[columns[i]] = rows[i]
                else:    
                    result = {"interface": "", "event_id": 0, "event_time": 0, "event_micro_time": 0, "transmit_time": 0}
        return result



#    def debug_data(self,data,depth):
#        indent = ''
#        for x in range(0,depth):
#            indent += '\t'
#        if isinstance(data,dict):
#            for key,value in data.iteritems():
#                print "{}{}: {}\n".format(indent, type(key), str(key))
#                print json.dumps(key)
#                self.debug_data(value, depth + 1)
#        elif isinstance(data,list):
#            for value in data:
#                self.debug_data(value, depth + 1)
#        else:
#            print "{}{}: {}\n".format(indent, type(data), str(data))
#            print json.dumps(data)



    def send_data(self, eventdata, spooledevent=False):
        # only send if there is data to be sent
        success = None
        if eventdata:
            tries = 0
            r = None
            # If at first you don't succeed, try again. And again, and again, and again, and again.
            # Server must return 200 OK or we will assume the delivery failed.
#            while tries <= 5:
            try:
                headers = {'User-Agent': self.useragent,
                'Content-Type': 'application/json'}
                url = self.send_to
                r = requests.post(url, headers=headers, data=json.dumps(eventdata), verify=self.verify)
                success = r.status_code
                if not r.status_code == 200:
                    if not spooledevent:
                        spooler.spool_data(json.dumps(eventdata))
                        errorstr = "Warning: server unable to accept events. Spooling events to file."
                        print >> sys.stderr, errorstr
                else:
                    self.write_last_event(eventdata)
            except ConnectionError as e:
                if not spooledevent:
                    spooler.spool_data(json.dumps(eventdata))
                    errorstr = "Warning: could not reach {}.".format(self.send_to)
                    print >> sys.stderr, errorstr
        return success
    

    def start_timer(self):
        if not self.timer.is_alive():
            print >> sys.stderr, "Warning: retrying in {} seconds.".format(self.retry_time)
            self.timer = threading.Timer(self.retry_time, self.unwind_spool)
            self.timer.start()


    def unwind_spool(self):
        self.timer.cancel()
        self.timer = threading.Timer(self.retry_time, self.unwind_spool)
        if spooler.spool_size() > 0:
            events = {}
            events['eventdata'] = spooler.unspool_data()
            events['sensor'] = socket.gethostname()
            success = 200 == self.send_data(events, True)
            if success:
                spooler.zero_spool()
            else:
                self.start_timer()
        

    def on_failed_send(eventdata):
        spooler.spool_data(json.dumps(eventdata))

    def on_created(self, event):
        self.timer.cancel()
        self.unwind_spool()
        ev_interface = self._interface_for_event(event)
        if ev_interface:
            events = self.build_data_to_send(interface=ev_interface, event=event, path=event.src_path)
            if ev_interface in events['eventdata'].keys() and len(events['eventdata'][ev_interface]) > 0:
                success = 200 == self.send_data(events)
                if not success: self.start_timer()



    def on_modified(self, event):
        self.timer.cancel()
        self.unwind_spool()
        ev_interface = self._interface_for_event(event)
        if ev_interface:
            events = self.build_data_to_send(interface=ev_interface, event=event, path=event.src_path)
            if ev_interface in events['eventdata'].keys() and len(events['eventdata'][ev_interface]) > 0:
                success = 200 == self.send_data(events)
                if not success: self.start_timer()



    def on_start(self):
        events = self.build_data_to_send(allfiles=True)
        if len(events['eventdata']) > 0:
            success = 200 == self.send_data(events)
            if not success: self.start_timer()

#!/usr/bin/env python
import settings, appdirs, os, json

spoolpath = os.path.join(appdirs.user_config_dir(settings.appname, settings.appauthor),
                'events.spool')

# write failed send data to a spool file
def spool_data(jsondata):
    with open(spoolpath, 'a') as f:
        f.write(jsondata + "\n")

# if unsent data can be sent, pull out the entire spool file for resend attempt
def unspool_data():
    events = {}
    with open(spoolpath, 'r') as f:
        for line in f:
            for instance, contents in json.loads(line)['eventdata'].iteritems():
                if instance not in events.keys():
                    events[instance] = intify_keys(contents)
                else:
                    events[instance].update(intify_keys(contents))
    return events
        

def intify_keys(eventdict):
    r = {}
    for key, val in eventdict.iteritems():
        r[int(key)] = val
    return r
            
def spool_size():
    if os.path.exists(spoolpath):
        return os.path.getsize(spoolpath)
    else:
        return 0

def zero_spool():
    if os.path.exists(spoolpath):
        os.remove(spoolpath)

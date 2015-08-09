#!/usr/bin/env python
import os
import appdirs
import shutil
import ConfigParser
import sqlite3
import requests
import settings


class Configure():
    def __init__(self):
        d = {}
        d['watch'] = {}
        confpath = appdirs.user_config_dir(settings.appname, settings.appauthor)
        #self.build_default_config(confpath, dest)
        config = ConfigParser.ConfigParser()
        config.read(os.path.join(confpath,'sneeze.conf'))
        
        required = [
            'destination',
            'useragent',
            'instance',
        ]

        instance = ''
        
        for entry in config.items('sneeze'):
            if entry[0] == 'instance':
                d['watch'][entry[1]] = {}
                instance = entry[1]
            elif entry[0] in ['path', 'pattern']:
                if entry[1] not in d['watch'][instance]:
                    d['watch'][instance][entry[0]] = entry[1]
                else:
                    msg = "Error in config file: {} has already been provided for this instance.".format(entry[0])  
                    raise ValueError(msg)
            else:
                d[entry[0]] = entry[1]

                
        # test required items existence
        # validate that required items exist
        if ('cert' in d.keys()) or ('key' in d.keys()):
            required.append(['cert', 'key'])

        for key in required:
            if key == 'instance':
                for instance, value in d['watch'].iteritems():
                    if 'path' not in value.keys():
                        msg = "Required item 'path' not specified for instance {} in config file.".format(instance)
                        raise ValueError(msg) 
            elif key not in d.keys():
                msg = "Required item {} not specified in config file.".format(key)
                raise ValueError(msg)
        
        # test item values
        # make sure sneeze.conf specifies valid paths to watch
        for interface, values in d['watch'].items():
            if not os.path.isdir(values['path']):
                raise ValueError("{} is not a valid directory.".format(values['path']))
    
        # make sure a retry time exists
        if 'retry_time' not in d.keys():
            d['retry_time'] = 60
        else:
            d['retry_time'] = int(d['retry_time'])
        
        # make sure verifycerts value exists and is valid
        if 'verifycerts' in d.keys():
            if d['verifycerts'] not in ['false', 'true']:
                raise ValueError("verifycerts must be 'false' or 'true'")
        else:
            d['verifycerts'] = 'true'

        # ensure the destination provided is not empty
        if len(d['destination']) < 1:
            raise ValueError("Destination must be provided.")
        else:
            if d['verifycerts'] == 'true':
                verify = True
            else:
                verify = False
            # test the connection
            headers = {'content-type': 'application/json', 'user-agent': d['useragent']}
            r = requests.post(d['destination'], data='{}', headers=headers, verify=verify)
        
        d['lastevent'] = os.path.join(confpath,'trace.db')

        self.confdata = d
        

def create_tracefile(dbfile):
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()

    c.execute('''CREATE TABLE lastevent
            (interface TEXT UNIQUE, event_id INT NOT NULL, event_time INT NOT NULL, event_micro_time INT NOT NULL, transmit_time REAL NOT NULL)''')

    conn.commit()
    conn.close()
    


def init(*args, **kwargs):
    confpath = appdirs.user_config_dir(settings.appname, settings.appauthor)
    if not os.path.exists(confpath):
        os.makedirs(confpath)

    # initialise the sent events database
    if not os.path.exists(os.path.join(confpath,'trace.db')):
        create_tracefile(os.path.join(confpath,'trace.db'))

    shutil.copy("sneeze.conf.default", os.path.join(confpath,"sneeze.conf"))
    print("Welcome to sneeze. To get started, please provide some initial configuration data.")
    print("A template config file has been placed in {}. ".format(confpath))
    print("Please edit this file before running sneeze.")

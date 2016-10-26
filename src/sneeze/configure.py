#!/usr/bin/env python
import os, sys
import appdirs
import shutil
import ConfigParser
import sqlite3
import requests
import settings


class Configure():
    def __init__(self, path=""):
        d = {}
        d['watch'] = {}
        confpath = appdirs.user_config_dir(settings.appname, settings.appauthor)
        if path:
            confpath = path

        print >> sys.stderr, "Loading config file {}...".format(path)

        #self.build_default_config(confpath, dest)
        config = ConfigParser.ConfigParser()
        config.read(os.path.join(confpath,'sneeze.conf'))
        
        required = [
            'destination',
            'useragent',
            'instance',
        ]

        instance = ''
        
        for section in config.sections():
            if section.startswith('instance'):
                instance = section.split(':')[1]
                d['watch'][instance] = {}
                
                path = config.get(section, 'path')
                d['watch'][instance]['path'] = path
                
                if config.has_option(section, 'pattern'):
                    pattern = config.get(instance, 'pattern')
                    d['watch'][instance]['pattern'] = pattern
            
        for (item, value) in config.items('sneeze'):
            d[item] = value

                        
        # test required items existence
        # validate that required items exist
        if ('cert' in d.keys()) or ('key' in d.keys()):
            required.append('cert')
            required.append('key')

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
                if not os.path.exists(d['verifycerts']):
                    raise ValueError("verifycerts must be 'false' or 'true', or be a path to a certificate file.")
        else:
            d['verifycerts'] = 'true'
        # ensure the destination provided is not empty
        if len(d['destination']) < 1:
            raise ValueError("Destination must be provided.")
        #else:
        #    if d['verifycerts'] == 'true':
        #        verify = True
        #    elif d['verifycerts'] == 'false':
        #        verify = False
        #    else:
        #        verify = d['verifycerts']
            # test the connection
            #headers = {'content-type': 'application/json', 'user-agent': d['useragent']}
            #if 'key' in d:
            #    r = requests.post(d['destination'], data='{}', headers=headers, 
            #        verify=verify, cert=(d['cert'], d['key']))
            #elif d['destination'].startswith('https'):
            #    r = requests.post(d['destination'], data='{}', headers=headers, verify=verify)
            #else:
            #    r = requests.post(d['destination'], data='{}', headers=headers)
        
        d['lastevent'] = os.path.join(confpath,'trace.db')
        self.confdata = d
        print >> sys.stderr, "Configuration loaded"
        

def create_tracefile(dbfile):
    print >> sys.stderr, "Creating database file {}".format(dbfile)
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()

    c.execute('''CREATE TABLE lastevent
            (interface TEXT UNIQUE, event_id INT NOT NULL, event_time INT NOT NULL, event_micro_time INT NOT NULL, transmit_time REAL NOT NULL)''')

    conn.commit()
    conn.close()
    


def init(*args, **kwargs):
    confpath = appdirs.user_config_dir(settings.appname, settings.appauthor)
    if not os.path.exists(confpath):
        print >> sys.stderr, "Writing configuration directory {}".format(confpath)
        os.makedirs(confpath)

    # initialise the sent events database
    if not os.path.exists(os.path.join(confpath,'trace.db')):
        create_tracefile(os.path.join(confpath,'trace.db'))

    shutil.copy("sneeze.conf.default", os.path.join(confpath,"sneeze.conf"))
    print("Welcome to sneeze. To get started, please provide some initial configuration data.")
    print("A template config file has been placed in {}. ".format(confpath))
    print("Please edit this file before running sneeze.")

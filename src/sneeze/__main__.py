#!/usr/bin/env python

import sys
import sneeze
import argparse
import configure

def main():
    parser = argparse.ArgumentParser()
    runmode = parser.add_subparsers(help="Initialise or run sneeze")
    parser_init = runmode.add_parser('init', help="Initialise sneeze")
    parser_run = runmode.add_parser('run', help="Run sneeze")
    
    parser_init.add_argument('-d', '--destination',
        help="Specify a remote HTTP/HTTPS destination to send logs to")
    parser_init.add_argument('--verify', default='store_true',
        help="Turn certificate verification on or off")
    parser_init.add_argument('-l',
        help="Specify a location to store the last event database. Defaults to user config directory.")
    parser_init.add_argument('-c',
        help="Specify a location to store the config file. Defaults to user config directory.")
    parser_init.set_defaults(func=init)

    parser_run.set_defaults(func=run)
    args = parser.parse_args()
    args.func(args)
        
        
def init(args):
    configure.init(args)


def run(args):
    sneeze.Sneeze(args)


if __name__ == "__main__":
    main()

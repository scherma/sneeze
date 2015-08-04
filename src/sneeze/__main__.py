#!/usr/bin/env python

import sys
import sneeze

def main(args=None):
    if args is None:
        args = sys.argv[1:]
        if args[0]:
            sneeze.Sneeze(args[0])
        else:
            sneeze.Sneeze()
    

if __name__ == "__main__":
    main()

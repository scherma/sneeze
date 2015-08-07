======
sneeze
======

------------------
Snort event pusher
------------------

Requirements:
* python2.7
* watchdog
* unified2
* requests

The purpose of sneeze is very simple:
* Watch a directory for updated or added unified2 files
* Parse new events out of those files
* Send the events in JSON format to a receiver via HTTP/HTTPS
* Track what events it has successfully sent

**Usage**

``sneeze init``
(edit config file)
``sneeze run``

sneeze will not attempt to dictate to the receiver anything about what to do with the event. Identifying the event's rule and text, feeding the event into a database or forwarding to another host, is entirely the responsibility of the receiver. sneeze only verifies that the receiver accepts the delivered event.

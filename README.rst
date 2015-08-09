======
sneeze
======

*Snort event pusher*

**Requirements**

* python2.7
* watchdog
* unified2
* requests

**Purpose**

* Watch a directory for updated or added unified2 files
* Parse new events out of those files
* Send the events in JSON format to a receiver via HTTP/HTTPS
* Track what events it has successfully sent

**Usage**

| ``sneeze init``
| *edit config file*
| ``sneeze run``
| 
**Behaviour**
 
| sneeze will not attempt to dictate to the receiver anything about what to do with the event. Identifying the event's rule and text description, feeding the event into a database or forwarding to another host, is entirely the responsibility of the receiver. sneeze only verifies that the receiver accepts the delivered event.
|
| A receiver for sneeze events should respond with a 200 OK code when an event has been accepted.
|
| When first run, sneeze will attempt to send all unified2 events in the specified directories to the receiver. New events are sent as soon as they are detected. If sneeze is unable to send an event, it will wait and try again (interval is configurable), and include any new events since the last successful one.

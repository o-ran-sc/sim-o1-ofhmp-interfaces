# Fault Management

Fault management consist of alarms, mechanisms to trigger alarms and alarm lists (whether active or not).


## Overall architecture

Independent on the used flavour, fault management works as follows:
1. any datastore data that is being loaded from the `/data` folder will be used by the the fault management module; all the loaded alarms will be further maintained by the fault-management feature.
2. `/data/fault-management/index.json` will then define a step-by-step recipe for triggering alarms and for maintaing alarms
3. unless commended otherwise, this step-by-step list will be repeated time and time again as long as the simulator is running

### fault-management/index.json

This file configures the fault generation. It contains two objects:
- *config* used to configure the fault-management feature
- *alarms* which contain the actual alarm steps. It is a *list* of steps that the fault-management system needs to play. Each step is defined as an object in the JSON list, and contains one or more instructions.

For *config* you can set the following parameters:
- *loop* - boolean set to true/false whether to loop the steps

In the example below, 2 steps are defined:
1. first step adds a time delay of 2 *seconds*
2. second step defined an alarm, as well as another time delay
```
{
    "config": {
        "loop": false
    },
    "alarms": [
        {
            "delay": 2
        },
        {
            "alarm": {
                // alarm id data
                // alarm data
            },
            "delay": 2
        }
    ]
}
```

The instructions currently implemented in the `fault-management` system are:
- *alarm* - implements an alarm; the content of the alarm is dictated by the current flavour notification schema
- *delay* - implements a time delay, in *seconds*

If both an *alarm* and a *delay* are defined within the same step, the alarm is executed first, then the delay.

The sum of all the delays defined by the step-list must be non-zero, otherwise the simulation will be stopeed with an exception.

### Internal alarm list
The internal alarm list is the actual data provider for the "alarm-list", "active alarm list" or any other form of alarm list depending on the current flavor.

When `/data/fault-management/index.json` step list is loaded, the fault-management internal alarm list can be either empty or can have some alarms (which were loaded as module data).

While executing "alarm" steps from the step list, there are 2 cases:
1. The alarm that is being executed already exists, which means that the fault-management system will **UPDATE** its state.
2. The alarm that is being executed does not exist, which means that the fault-management system will **CREATE** it within its internal alarm list, and from that time on, the alarm will exist.


### Examples

#### Alarm-list empty, raising and clearing alarm every minute
index.json
```
{
    "config": {
        "loop": false
    },
    "alarms": [
        {
            "alarm": {
                // alarm1

                // raising alarm
            },
            "delay": 30
        },
        {
            "alarm": {
                // alarm1

                // clearing alarm
            },
            "delay": 30
        }
    ]
}
```

#### Alarm-list contains alarm1, raising alarm1 each 10 seconds, and clearing it after 1 second
flavour-module-data.json
```
{
    ...active-alarm: {
        // data for alarm1
        // including the fact that is **SET**
    }
}
```

index.json
```
{
    "config": {
        "loop": false
    },
    "alarms": [
        {
            "delay": 1
        }
        {
            "alarm": {
                // alarm1

                // clearing alarm
            },
            "delay": 9
        },
        {
            "alarm": {
                // alarm1

                // raising alarm
            },
        }
    ]
}
```
#### Raising and clearing 10 alarms at once
index.json
```
{
    "config": {
        "loop": false
    },
    "alarms": [
        {
            "alarm": {
                // alarm1

                // raising alarm
            }
        },
        {
            "alarm": {
                // alarm2

                // raising alarm
            }
        },
        .....
        {
            "alarm": {
                // alarm10

                // raising alarm
            }
        },
        {
            "delay": 10
        },
        {
            "alarm": {
                // alarm1

                // clearing alarm
            }
        },
        {
            "alarm": {
                // alarm2

                // clearing alarm
            }
        },
        .....
        {
            "alarm": {
                // alarm10

                // clearing alarm
            }
        },
        {
            "delay": 10
        }
    ]
}
```

## Initial Alarm Time Stamps

In the `/data/ietf-alarms-operational.json` file, the initial alarms may have a triplet of timestamps set:

```
"time-created": "2024-05-11T11:22:30Z",
"last-raised": "2024-05-11T11:22:33Z",
"last-changed": "2024-05-11T11:22:33Z",
```
If these timestamps are set, the fault-management system will use them as the initial timestamps for the alarms that are being raised.
If these timestamps are not set, the fault-management system will use the current time as the initial timestamps for the alarms that are being raised.

Currently, the field `last-changed` is required to be set, otherwise the initial alarm will not be raised.

## Flavours

The flavour is automatically detected based on the currently installed schema files:
- if more than one flavour is present, the simulator will end with an exception
- if no flavour is present, the fault-management feature will be turned off
- otherwise, the fault-management system will run using the currently installed flavour

The current fault-management flavours implemented and recognized by the simulator are:

### ietf-alarms

checkAL add pyang data on the schema that is being taken into account

### o-ran-fm

Not yet implemented.

## REST API

Fault-Management module adds endpoints to PyNTS REST API:
- /fault-management
    - method: GET
    - returns current status of the fault-management module

- /fault-management/counters
    - method GET
    - returns current alarm counters

- /fault-management/start
    - method POST
    - starts fault-management alarm steps
    - does not work if FM is already started
    - data should be a JSON with the same format as index.json
    - returns a message and current status of the fault-management system

- /fault-management/stop
    - method POST
    - stops fault-management alarm steps
    - does not work if FM is already stopped
    - no data is needed
    - returns a message and current status of the fault-management system

- /fault-management/counters/clear
    - method POST
    - clears alarm counters
    - no data is needed
    - returns current alarm counters (with 0 value)

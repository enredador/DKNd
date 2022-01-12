# DKNd

Python program for integrating a BRP069A62 Daikin Altherma LAN adapter with home assistant


## Background

This program can be run in "daemon" mode (for instance, under systemd).
It periodically polls altherma sensors and send the values to the configured homeassistant sensors.

Additionally it can be run as a simple command to get a sensor value or set a value or a mode.

It has partial support for schedules management. It can load a schedule file to or get the schedule from the altherma system.

It communicates locally with the BRP069A62 and does not uses the DAIKIN cloud. It uses the DAIKIN websockets interface.
The WS endpoints and related details were initially obtained from contributors in the forums referenced below and were completed
using reverse engineering using the deprecated "Daikin Online Controller" app.
It is uncertain that this process could be replicated with the new "Daikin Residential Controller" app. I do not know if this local approach
will keep on working with the new firmware updates proposed by the new "Daikin Residential Controller" app.

The WS endpoints accepted change as the machine setup is changed. This program has only considered "Room Temperature" (RT) and "Leaving Water Temperature" (LWT)
modes for heating and cooling, and "Reheat + Scheduling" mode for domestic water heating. Completing the WS endpoints for all working modes  is a pending task.
The program now has partial support for working with both RT and LWT modes.


## Requirements:

This program is tested with a BRP069A62 LAN adapter for Daikin Altherma 2, firmware 436CC135000.
Although not tested, it may work with other Altherma models, firmware versions  or the BRP069A61 LAN adapter.

It has been tested in the same Raspberry Pi OS where homeasssistant is running.

Requires:

 - `python3`
 - This python libraries need to be installed:
   * `requests`
   * `PyYaml`
   * `websocket-client`


## Usage

- Command line help:
     - `python3 bin/DKN.py --config lib/DKN.yaml --help`
     - `python3 bin/DKN.py --config lib/DKN.yaml sensord --help`
     - `python3 bin/DKN.py --config lib/DKN.yaml get --help`
     - `python3 bin/DKN.py --config lib/DKN.yaml set --help`
     - `python3 bin/DKN.py --config lib/DKN.yaml schedules_get --help`
     - `python3 bin/DKN.py --config lib/DKN.yaml schedules_set --help`
- Examples:
    - Get LWT current value:
      `python3 bin/DKN.py --config lib/DKN.yaml get LWTcurrent`
    - Switch off CH:
      `python3 bin/DKN.py --config lib/DKN.yaml set CHonoff off`
    - Switch off CH and update homeassistant:
      `python3 bin/DKN.py --config lib/DKN.yaml set CHonoff off --updateHA`

## Setup

## Configuration

## TODO

____

## Sources:

Using the WS endpoints was learned from  posts in these forums:

 - <https://community.openenergymonitor.org/t/hack-my-heat-pump-and-publish-data-onto-emoncms/2551/32>
 - <https://community.openhab.org/t/how-to-integrate-daikin-altherma-lt-heat-pump/16488/16>
 
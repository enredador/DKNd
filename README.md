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
    - Get LWT current value:\
      `python3 bin/DKN.py --config lib/DKN.yaml get LWTcurrent`
    - Switch off CH:\
      `python3 bin/DKN.py --config lib/DKN.yaml set CHonoff off`
    - Switch off CH and update homeassistant:\
      `python3 bin/DKN.py --config lib/DKN.yaml set CHonoff off --updateHA`
    - Run in daemon mode for all possible items in RT mode, polling each 30 seconds:
      `python3 bin/DKN.py --config lib/DKN.yaml --rt sensord --delay 30`
    - Get shedule for DHW from altherma system:\
      `python3 bin/DKN.py --config lib/DKN.yaml schedules_get DHWlistHeat`
    - Upload schedule for DHW that is stored in lib/DKN.dict:\
      `python3 bin/DKN.py --config lib/DKN.yaml --programs lib/DKN.dict schedules_set DHWlistHeat`

Creating or editing the schedules file is out of the scope of `DKN.py`. A php code is provided in the directory `www`to help in this task when it is installed in
he appropriate directory for your web server and called from a web browser.
The auxiliary programs that it needs are also provided. No documentation for that is provided in this preliminar upload.

## Configuration

### Program configuration

Configuration is partially made editing the provided `lib/DKN.yaml` and should be self-explicative. Connection data for LAN adapter and homeassistant,
and ong-lived access token for homeassistant API must be specified here. The rest of the options (working mode, schedule file and polling interval) can be
set up here for default values but can be overrided with command-line options.

The python code (DKN.py) can be edited for changing some data, as the homeassistant entity names or the attributes sent to them in updates.
Changing this data to the configuration file is also a pending task. 

### Homeassistant configuration

Most items are `sensor` or `binary_sensor` entities that are created automatically in homeassistant with the first update. If a sensor needs to be available
on HA startup, it can be defined (see example in `HA` directory).
However, some other entities should be created in homeassistant, such `switch` or `input_select` for using some items. In the `HA` directory some files are provided
to help in the task and may be adapted to each particular installation. The files provided are used in a docker homeassistant instance.
Automations are also needed to sync homeassistant actuators (e.g. `input_select`) to the altherma system. Please consult `HA` directory examples.

## Setup

Copy DKN.py (python code) and DKN.yaml (configuration) files in selected directories. For example, `/home/pi/bin` for `DKN.py`
and `/home/pi/lib` for `DKN.yaml`, are the recommended paths. If it is to be running in daemon mode, `systemd` can be used to manage it. An example
of the service file can be found in the `systemd` directory. This file should be installed in  `/etc/systemd/system/altherma.service`. After that, the following
commands should be executed:

- `sudo systemctl daemon-reload`
- `sudo systemctl enable altherma`
- `sudo systemctl start altherma`

Logs can then be accessed with `journalctl -u altherma` (last log lines with `journalctl -fu altherma`)

----
## Sources:

Using the WS endpoints was learned from  posts in these forums:

 - <https://community.openenergymonitor.org/t/hack-my-heat-pump-and-publish-data-onto-emoncms/2551/32>
 - <https://community.openhab.org/t/how-to-integrate-daikin-altherma-lt-heat-pump/16488/16>
 
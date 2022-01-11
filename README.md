# DKNd

Python program for integrating a BRP069A62 Daikin Altherma LAN adapter with home assistant


## Background

This program can be run in "daemon" mode (for instance, under systemd).
It periodically polls altherma sensors and send the values to the configured homeassistant sensors.

Additionally it can be run as a simple command to get a sensor value or set a value or a mode.

It has partial support for schedule management.

## Requirements:

This program is tested with a BRP069A62 LAN adapter for Daikin Altherma 2, firmware 436CC135000.
Although not tested, it may work with other Altherma models, firmware versions  or the BRP069A61 LAN adapter.


Requires:

 - `python3`
 - python libraries:
   * `requests`
   * `PyYaml`
   * `websocket-client`


## Usage

- Command line help:
- - `python3 bin/DKN.py --config lib/DKN.yaml --help`
- - `python3 bin/DKN.py --config lib/DKN.yaml get --help`
- - `python3 bin/DKN.py --config lib/DKN.yaml set --help`

- Get LWT current value `python3 bin/DKN.py --config lib/DKN.yaml get LWTcurrent`
- Switch off CH  `python3 bin/DKN.py --config lib/DKN.yaml set CHonoff off`
- Switch off CH and update homeassistant: `python3 bin/DKN.py --config lib/DKN.yaml set CHonoff off --updateHA`

## Setup

## Configuration

## TODO

____

## Sources:

Using the WS endpoints was learned from  posts in these forums:

 - <https://community.openenergymonitor.org/t/hack-my-heat-pump-and-publish-data-onto-emoncms/2551/32>
 - <https://community.openhab.org/t/how-to-integrate-daikin-altherma-lt-heat-pump/16488/16>
 
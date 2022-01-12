#!/usr/bin/env python3
# coding=utf-8

# Code written for communicating with a
# DAIKIN ALTHERMA system using BRP069A62 Daikin LAN Adapter

# This code can be used, copied and distributed freely,
# provided that its origin is mentioned
#
# It is provided without any warranty, explicit or implicit.
# Please use it at your own risk.
#
# Author: José Miguel Goñi Menoyo (@enredador)
#
#  v1.0 23/10/2019
#  v2.0 23/03/2020
#  v3.0 26/08/2021 Support of LWT mode
#  v4.0 12/01/2022 Bug fixes and documentation
#
# Libraries
#
from websocket import create_connection
import json, requests, ast
import argparse
import yaml, pprint
import time, sys, string, random

#
# Default values
#

# DELAY_INT:    Default value for lolling interval, in seconds
#
DELAY_INT   = 300


# SCHEDULES:     File containing heating, cooling and DWH schedules
#
PROGRAMS="DKN.dict"

# DKNCONFIG:    Config file
#
DKNCONFIG="DKN.yaml"


####################################################################################################
# Items for the webservices endpoints from BRP069A62 Daikin LAN Adapter 
####################################################################################################
#
# Exclusive for RT (room temperature) mode
# 
read_items_rt = {
  "CHsetptemp":      {"endpoint": "/[0]/MNAE/1/Operation/TargetTemperature", # 22-35 25-15
                      "HA": {"device": "sensor.ch_setpoint",
                             "attributes":{"friendly_name": "Temperatura de consigna (CH)",
                                           "device_class":"temperature",
                                           "unit_of_measurement":"°C"}}},
  "CHsetptempauto": {"endpoint": "/[0]/MNAE/1/Operation/RoomTemperatureAuto",
                      "HA": {"device": "sensor.ch_setpoint_auto",
                             "attributes":{"friendly_name": "Temperatura de consigna auto (CH)",
                                           "device_class":"temperature",
                                           "unit_of_measurement":"°C"}}},
  "CHsetptempcool": {"endpoint": "/[0]/MNAE/1/Operation/RoomTemperatureCooling",
                      "HA": {"device": "sensor.ch_setpoint_cool",
                             "attributes":{"friendly_name": "Temperatura de consigna cooling (CH)",
                                           "device_class":"temperature",
                                           "unit_of_measurement":"°C"}}},
  "CHsetptempheat": {"endpoint": "/[0]/MNAE/1/Operation/RoomTemperatureHeating",
                      "HA": {"device": "sensor.ch_setpoint_heat",
                             "attributes":{"friendly_name": "Temperatura de consigna heating (CH)",
                                           "device_class":"temperature",
                                           "unit_of_measurement":"°C"}}},
  "CHisOverride":    {"endpoint": "/[0]/MNAE/1/UnitStatus/TargetTemperatureOverruledState",
                      "HA": {"device": "binary_sensor.dkn_ch_isoverride",
                             "values": {0: "off", 1: "on"},
                              "attributes":{"friendly_name": "Consigna forzada (CH)",
                                            "icon":"mdi:hand-left"}}},
  "CHactive":  {"endpoint": "/[0]/MNAE/1/Schedule/Active",
                      "HA": {"device": "input_select.ch_active",
                             "values_h": {0: "calef_predefinido_1",
                                          1: "calef_predefinido_2",
                                          2: "calef_predefinido_3",
                                          3: "calef_fin_de_semana",
                                          4: "calef_semana",
                                          5: "calef_casa_vacia"},
                             "values_c": {0: "refr_predefinido_1",
                                          1: "refr_predefinido_2",
                                          2: "refr_predefinido_3",
                                          3: "refr_usuario"},
                             "attributes":{"friendly_name": "Programa activo CH",
                                           "initial": "null",
                                           "options": [ "calef_semana",        "calef_fin_de_semana", "calef_casa_vacia",
                                                        "calef_predefinido_1", "calef_predefinido_2", "calef_predefinido_3",
                                                        "refr_usuario",
                                                        "refr_predefinido_1",  "refr_predefinido_2",  "refr_predefinido_3"],
                                           "icon": "mdi:thermomether"}}},
}

#
# For RT (room temperature) and LWT (leaving water temperature) modes
# 
read_items = {
  "CHmode":          {"endpoint": "/[0]/MNAE/1/Operation/OperationMode",  # heating cooling auto
                      "HA": {"device": "sensor.dkn_ch_mode",
                             "attributes":{"friendly_name": "Modo de funcionamiento (CH)", 
                                           "icon": "mdi:arrow-decision-outline"}}},
  "CHonoff":         {"endpoint": "/[0]/MNAE/1/Operation/Power",  # on standby
                      "HA": {"device": "binary_sensor.dkn_ch_isonoff",
                             "values": {"standby": "off", "on": "on"},
                             "attributes":{"friendly_name": "Encendido/Apagado (CH)", 
                                           "device_class":"power"}}},
  "CHintemp":        {"endpoint": "/[0]/MNAE/1/Sensor/IndoorTemperature",
                      "HA": {"device": "sensor.dkn_in_temp",
                             "attributes":{"friendly_name": "Temperatura interior (CH)",
                                           "device_class":"temperature",
                                           "unit_of_measurement":"°C"}}},
  "CHouttemp":       {"endpoint": "/[0]/MNAE/1/Sensor/OutdoorTemperature",
                      "HA": {"device": "sensor.dkn_out_temp",
                             "attributes":{"friendly_name": "Temperatura exterior",
                                           "device_class":"temperature",
                                           "unit_of_measurement":"°C"}}},
  "CHisActive":      {"endpoint": "/[0]/MNAE/1/UnitStatus/ActiveState",
                      "HA": {"device": "binary_sensor.dkn_ch_isactive",
                             "values": {0: "off", 1: "on"},
                              "attributes":{"friendly_name": "Activo/Inactivo (CH)", 
                                            "device_class":"plug"}}},
  "CHctrmode":       {"endpoint": "/[0]/MNAE/1/UnitStatus/ControlModeState",
                      "HA": {"device": "sensor.dkn_ch_ctrmode",
                              "attributes":{"friendly_name": "Modo de control (CH)", 
                                            "icon": "mdi:home-thermometer-outline"}}},
  "CHisEmergency":   {"endpoint": "/[0]/MNAE/1/UnitStatus/EmergencyState",
                      "HA": {"device": "binary_sensor.dkn_ch_isemergency",
                             "values": {0: "off", 1: "on"},
                              "attributes":{"friendly_name": "Emergencia (CH)",
                                            "device_class": "problem"}}},
  "CHisError":       {"endpoint": "/[0]/MNAE/1/UnitStatus/ErrorState",
                      "HA": {"device": "binary_sensor.dkn_ch_iserror",
                             "values": {0: "off", 1: "on"},
                              "attributes":{"friendly_name": "Error (CH)",
                                            "device_class": "problem"}}},
  "CHisWarning":     {"endpoint": "/[0]/MNAE/1/UnitStatus/WarningState",
                      "HA": {"device": "binary_sensor.dkn_ch_iswarning",
                             "values": {0: "off", 1: "on"},
                              "attributes":{"friendly_name": "Warning (CH)", 
                                            "device_class": "problem"}}},
  "CHisInstaller":   {"endpoint": "/[0]/MNAE/1/UnitStatus/InstallerState",
                      "HA": {"device": "binary_sensor.dkn_ch_isinstaller",
                             "values": {0: "off", 1: "on"},
                              "attributes":{"friendly_name": "Modo instalador (CH)",
                                            "icon":"mdi:wrench-outline"}}},
  "LWTsetpauto":    {"endpoint": "/[0]/MNAE/1/Operation/LeavingWaterTemperatureAuto",  # LWT setp
                      "HA": {"device": "sensor.dkn_lwt_setpauto",
                             "attributes":{"friendly_name": "Auto LWT setpoint",
                                           "device_class":"temperature",
                                           "unit_of_measurement":"°C"}}},
  "LWTsetpcool":    {"endpoint": "/[0]/MNAE/1/Operation/LeavingWaterTemperatureCooling",  # LWT setp
                      "HA": {"device": "sensor.dkn_lwt_setpcooling",
                             "attributes":{"friendly_name": "Cooling LWT setpoint",
                                           "device_class":"temperature",
                                           "unit_of_measurement":"°C"}}},
  "LWTsetpheat":    {"endpoint": "/[0]/MNAE/1/Operation/LeavingWaterTemperatureHeating",  # LWT setp
                      "HA": {"device": "sensor.dkn_lwt_setpheating",
                             "attributes":{"friendly_name": "Heating LWT setpoint",
                                           "device_class":"temperature",
                                           "unit_of_measurement":"°C"}}},
  "LWTcurrent":     {"endpoint": "/[0]/MNAE/1/Sensor/LeavingWaterTemperatureCurrent",  # LWT curr
                      "HA": {"device": "sensor.dkn_lwt_current",
                             "attributes":{"friendly_name": "Current LW temperature",
                                           "device_class":"temperature",
                                           "unit_of_measurement":"°C"}}},
  "LWToffsetauto":  {"endpoint": "/[0]/MNAE/1/Operation/LeavingWaterTemperatureOffsetAuto",  # LWT offset
                      "HA": {"device": "sensor.dkn_lwt_offsetauto",
                             "attributes":{"friendly_name": "Auto LWT offset",
                                           "device_class":"temperature",
                                           "unit_of_measurement":"°C"}}},
  "LWToffsetcool":  {"endpoint": "/[0]/MNAE/1/Operation/LeavingWaterTemperatureOffsetCooling",  # LWT offset
                      "HA": {"device": "sensor.dkn_lwt_offsetcooling",
                             "attributes":{"friendly_name": "Cooling LWT offset",
                                           "device_class":"temperature",
                                           "unit_of_measurement":"°C"}}},
  "LWToffsetheat":  {"endpoint": "/[0]/MNAE/1/Operation/LeavingWaterTemperatureOffsetHeating",  # LWT offset
                      "HA": {"device": "sensor.dkn_lwt_offsetheating",
                             "attributes":{"friendly_name": "Heating LWT offset",
                                           "device_class":"temperature",
                                           "unit_of_measurement":"°C"}}},
  "DHWmode":         {"endpoint": "/[0]/MNAE/2/Operation/OperationMode", # reheat_schedule
                      "HA": {"device": "sensor.dkn_dhw_mode",
                             "attributes":{"friendly_name": "Modo de funcionamiento (ACS)", 
                                           "icon": "mdi:water-boiler"}}},
  "DHWonoff":        {"endpoint": "/[0]/MNAE/2/Operation/Power", # on standby
                      "HA": {"device": "binary_sensor.dkn_dhw_isonoff",
                             "values": {"standby": "off", "on": "on"},
                             "attributes":{"friendly_name": "Encendido/Apagado (ACS)", 
                                           "device_class":"power"}}},
  "DHWpowerful":     {"endpoint": "/[0]/MNAE/2/Operation/Powerful", # 0 1
                      "HA": {"device": "binary_sensor.dkn_dhw_powerful",
                             "values": {0: "off", 1: "on"},
                             "attributes":{"friendly_name": "Modo resistencia (ACS)",
                                           "icon":"mdi:arm-flex-outline"}}},
  "DHWsetptemp":     {"endpoint": "/[0]/MNAE/2/Operation/TargetTemperature", # 30-50
                      "HA": {"device": "sensor.dhw_setpoint",
                             "attributes":{"friendly_name": "Temperatura de consigna (ACS)",
                                           "device_class":"temperature",
                                           "unit_of_measurement":"°C"}}},
  "DHWsetptempheat": {"endpoint": "/[0]/MNAE/2/Operation/DomesticHotWaterTemperatureHeating", # 30-50
                      "HA": {"device": "sensor.dhw_setpoint_heating",
                             "attributes":{"friendly_name": "Temperatura de calentamiento (ACS)",
                                           "device_class":"temperature",
                                           "unit_of_measurement":"°C"}}},
  "DHWtanktemp":     {"endpoint": "/[0]/MNAE/2/Sensor/TankTemperature",
                      "HA": {"device": "sensor.dkn_dhw_temp",
                             "attributes":{"friendly_name":  "Temperatura del ACS",
                                           "device_class":"temperature",
                                           "unit_of_measurement":"°C"}}},
  "DHWisActive":     {"endpoint": "/[0]/MNAE/2/UnitStatus/ActiveState",
                      "HA": {"device": "binary_sensor.dkn_dhw_isactive",
                             "values": {0: "off", 1: "on"},
                             "attributes":{"friendly_name": "Activo/Inactivo (ACS)", 
                                           "device_class":"plug"}}},
  "DHWisEmergency":  {"endpoint": "/[0]/MNAE/2/UnitStatus/EmergencyState",
                      "HA": {"device": "binary_sensor.dkn_dhw_isemergency",
                             "values": {0: "off", 1: "on"},
                             "attributes":{"friendly_name": "Emergencia (DHW)",
                                           "device_class": "problem"}}},
  "DHWisError":      {"endpoint": "/[0]/MNAE/2/UnitStatus/ErrorState",
                      "HA": {"device": "binary_sensor.dkn_dhw_iserror",
                             "values": {0: "off", 1: "on"},
                             "attributes":{"friendly_name": "Error (DHW)",
                                           "device_class": "problem"}}},
  "DHWisInstaller":  {"endpoint": "/[0]/MNAE/2/UnitStatus/InstallerState",
                      "HA": {"device": "binary_sensor.dkn_dhw_isinstaller",
                             "values": {0: "off", 1: "on"},
                              "attributes":{"friendly_name": "Modo instalador (DHW)",
                                            "icon":"mdi:wrench-outline"}}},
  "DHWisReheat":     {"endpoint": "/[0]/MNAE/2/UnitStatus/ReheatState",
                      "HA": {"device": "binary_sensor.dkn_dhw_isreheat",
                             "values": {0: "off", 1: "on"},
                              "attributes":{"friendly_name": "Recalentamiento (DHW)",
                                            "device_class":"heat"}}},
  "DHWisOverride":   {"endpoint": "/[0]/MNAE/2/UnitStatus/TargetTemperatureOverruledState",
                      "HA": {"device": "binary_sensor.dkn_dhw_isoverride",
                             "values": {0: "off", 1: "on"},
                              "attributes":{"friendly_name": "Consigna forzada (DHW)",
                                            "icon":"mdi:hand-left"}}},
  "DHWisWarning":    {"endpoint": "/[0]/MNAE/2/UnitStatus/WarningState",
                      "HA": {"device": "binary_sensor.dkn_dhw_iswarning",
                             "values": {0: "off", 1: "on"},
                              "attributes":{"friendly_name": "Warning (DHW)", 
                                            "device_class": "problem"}}},
  "DHWactive": {"endpoint": "/[0]/MNAE/2/Schedule/Active",
                      "HA": {"device": "input_select.dhw_active",
                             "values_h": {0: "acs_predefinido_1",
                                          1: "acs_predefinido_2",
                                          2: "acs_predefinido_3",
                                          3: "acs_usuario"},
                             "attributes":{"friendly_name": "Programa activo DHW",
                                           "initial": "null",
                                           "options": [ "acs_usuario", "acs_predefinido_1", "acs_predefinido_2", "acs_predefinido_3"],
                                           "icon": "mdi:thermomether"}}}
}

#
# Exclusive for RT (room temperature) mode
# 
write_items_rt = {
  "CHsetptemp":     {"endpoint": "/[0]/MNAE/1/Operation/TargetTemperature",
                     "numeric":   "22-35,15-25"},
  "CHsetptempauto": {"endpoint": "/[0]/MNAE/1/Operation/RoomTemperatureAuto",
                     "numeric":   "22-35,15-25"},
  "CHsetptempcool": {"endpoint": "/[0]/MNAE/1/Operation/RoomTemperatureCooling",
                     "numeric":   "15-25"},
  "CHsetptempheat": {"endpoint": "/[0]/MNAE/1/Operation/RoomTemperatureHeating",
                      "numeric":   "22-35"},
  "CHactive":       {"endpoint": "/[0]/MNAE/1/Schedule/Active",
                     "values":   {"calef_predefinido_1": ["heat", 0],
                                  "calef_predefinido_2": ["heat", 1],
                                  "calef_predefinido_3": ["heat", 2],
                                  "calef_fin_de_semana": ["heat", 3],
                                  "calef_semana":        ["heat", 4],
                                  "calef_casa_vacia":    ["heat", 5],
                                  "refr_predefinido_1":  ["cool", 0],
                                  "refr_predefinido_2":  ["cool", 1],
                                  "refr_predefinido_3":  ["cool", 2],
                                  "refr_usuario":        ["cool", 3]},
                     "payload": { "heat":
                                    "\"{{\\\"data\\\":{{\\\"path\\\":\\\"/MNCSEBase/MNAE/1/schedule/List/Heating/la\\\",\\\"id\\\": {0}}}}}\"",
                                  "cool":
                                    "\"{{\\\"data\\\":{{\\\"path\\\":\\\"/MNCSEBase/MNAE/1/schedule/List/Cooling/la\\\",\\\"id\\\": {0}}}}}\""}},
}

#
# For RT (room temperature) and LWT (leaving water temperature) modes
# 
write_items = {
  "CHmode":         {"endpoint":  "/[0]/MNAE/1/Operation/OperationMode",
                     "values":    {"heating": ["std", "\"heating\""],
                                   "cooling": ["std", "\"cooling\""],
                                   "auto":    ["std", "\"auto\""]},
                     "payload":   {"std": "{}"}},
  "CHonoff":        {"endpoint": "/[0]/MNAE/1/Operation/Power",
                     "values":    {"on":  ["std", "\"on\""],
                                   "off": ["std", "\"standby\""]},
                     "payload":   {"std": "{}"}},
  "LWTsetpauto":    {"endpoint": "/[0]/MNAE/1/Operation/LeavingWaterTemperatureAuto",
                     "numeric":   "15-25,22-35"},
  "LWTsetpcool":    {"endpoint": "/[0]/MNAE/1/Operation/LeavingWaterTemperatureCooling",
                     "numeric":   "16-22"},
  "LWTsetpheat":    {"endpoint": "/[0]/MNAE/1/Operation/LeavingWaterTemperatureHeating",
                     "numeric":   "28-40"},
  "DHWonoff":       {"endpoint": "/[0]/MNAE/2/Operation/Power",
                     "values":    {"on":  ["std", "\"on\""],
                                   "off": ["std", "\"standby\""]},
                     "payload":   {"std": "{}"}},
  "DHWpowerful":    {"endpoint": "/[0]/MNAE/2/Operation/Powerful",
                     "values":    {"off": ["std", "0"],
                                   "on":  ["std", "1"]},
                     "payload":   {"std": "{}"}},
  "DHWsetptemp":    {"endpoint": "/[0]/MNAE/2/Operation/TargetTemperature",
                     "numeric":   "30-50"},
  "DHWsetptempheat": {"endpoint": "/[0]/MNAE/2/Operation/DomesticHotWaterTemperatureHeating",
                      "numeric":   "30-50"},
  "DHWactive":    {"endpoint": "/[0]/MNAE/2/Schedule/Active",
                   "values":   {"acs_predefinido_1": ["heat", 0],
                                "acs_predefinido_2": ["heat", 1],
                                "acs_predefinido_3": ["heat", 2],
                                "acs_usuario":       ["heat", 3]},
                   "payload":  {"heat":
                                 "\"{{\\\"data\\\":{{\\\"path\\\":\\\"/MNCSEBase/MNAE/2/schedule/List/Heating/la\\\",\\\"id\\\": {0}}}}}\""}},
  }


#
# Schedule management items
#

#
# Exclusive for RT (room temperature) mode
# 
schedule_items_rt = {
  "CHlistCool":   {"endpoint": "/[0]/MNAE/1/Schedule/List/Cooling",
                   "programs":4, "actions": 6},
  "CHlistHeat":   {"endpoint": "/[0]/MNAE/1/Schedule/List/Heating",
                   "programs":6, "actions": 6},
  }

schedule_read_items_rt = {
  "CHdefault":    {"endpoint": "/[0]/MNAE/1/Schedule/Default"},
  "CHnext":       {"endpoint": "/[0]/MNAE/1/Schedule/Next"}
  }

#
# For RT (room temperature) and LWT (leaving water temperature) modes
# 
schedule_items = {
  "DHWlistHeat":  {"endpoint": "/[0]/MNAE/2/Schedule/List/Heating",
                   "programs":4, "actions": 4}
  }

#
# For RT (room temperature) and LWT (leaving water temperature) modes
# 
schedule_read_items = {
  "DHWnext":      {"endpoint": "/[0]/MNAE/2/Schedule/Next"}
  }

#
# Not working items in my installation
# 
not_working_items = {
  "0/ConnectionTest":                     "/[0]/MNAE/0/ConnectionTest",
  "0/ConnectionTest":                     "/[0]/MNAE/0/ConnectionTest",
  "1/Operation/ComfortMode":              "/[0]/MNAE/1/Operation/ComfortMode",
  "1/Consumption":                        "/[0]/MNAE/1/Consumption",
  "1/Hybrid/ActiveState":                 "/[0]/MNAE/1/Hybrid/ActiveState",
  "1/Hybrid/ElectricityPrice/High":       "/[0]/MNAE/1/Hybrid/ElectricityPrice/High",
  "1/Hybrid/ElectricityPrice/Low":        "/[0]/MNAE/1/Hybrid/ElectricityPrice/Low",
  "1/Hybrid/ElectricityPrice/Mid":        "/[0]/MNAE/1/Hybrid/ElectricityPrice/Mid",
  "1/Hybrid/GasPrice":                    "/[0]/MNAE/1/Hybrid/GasPrice",
  "2/Consumption":                        "/[0]/MNAE/2/Consumption",
  "2/Operation/ReheatTargetTemperature":  "/[0]/MNAE/2/Operation/ReheatTargetTemperature",
  "1/Reboot":                             "/[0]/MNAE/1/Reboot"
}

#
# Not tested or not used
# 
pending_items = {
  "0/DateTime":                           "/[0]/MNAE/0/DateTime",
  "0/Error":                              "/[0]/MNAE/0/Error",
  "0/NetworkSettings":                    "/[0]/MNAE/0/NetworkSettings",
  "0/UnitProfile":                        "/[0]/MNAE/0/UnitProfile",
  "0/UnitStatus/ErrorState":              "/[0]/MNAE/0/UnitStatus/ErrorState",
  "1/ChildLock/LockedState":              "/[0]/MNAE/1/ChildLock/LockedState",
  "1/ChildLock/PinCode":                  "/[0]/MNAE/1/ChildLock/PinCode",
  "1/Error":                              "/[0]/MNAE/1/Error",
  "1/Holiday/EndDate":                    "/[0]/MNAE/1/Holiday/EndDate",
  "1/Holiday/HolidayState":               "/[0]/MNAE/1/Holiday/HolidayState",
  "1/Holiday/StartDate":                  "/[0]/MNAE/1/Holiday/StartDate",
  "1/UnitIdentifier/Icon":                "/[0]/MNAE/1/UnitIdentifier/Icon",
  "1/UnitIdentifier/Name":                "/[0]/MNAE/1/UnitIdentifier/Name",
  "1/UnitInfo/Manufacturer":              "/[0]/MNAE/1/UnitInfo/Manufacturer",
  "1/UnitInfo/ModelNumber":               "/[0]/MNAE/1/UnitInfo/ModelNumber",
  "1/UnitInfo/SerialNumber":              "/[0]/MNAE/1/UnitInfo/SerialNumber",
  "1/UnitInfo/UnitType":                  "/[0]/MNAE/1/UnitInfo/UnitType",
  "1/UnitInfo/Version/IndoorSettings":    "/[0]/MNAE/1/UnitInfo/Version/IndoorSettings",
  "1/UnitInfo/Version/IndoorSoftware":    "/[0]/MNAE/1/UnitInfo/Version/IndoorSoftware",
  "1/UnitInfo/Version/OutdoorSoftware":   "/[0]/MNAE/1/UnitInfo/Version/OutdoorSoftware",
  "1/UnitInfo/Version/RemoconSettings":   "/[0]/MNAE/1/UnitInfo/Version/RemoconSettings",
  "1/UnitInfo/Version/RemoconSoftware":   "/[0]/MNAE/1/UnitInfo/Version/RemoconSoftware",
  "1/UnitProfile":                        "/[0]/MNAE/1/UnitProfile",
  "1/UnitStatus/WeatherDependentState":   "/[0]/MNAE/1/UnitStatus/WeatherDependentState",
  "2/ChildLock/LockedState":              "/[0]/MNAE/2/ChildLock/LockedState",
  "2/ChildLock/PinCode":                  "/[0]/MNAE/2/ChildLock/PinCode",
  "2/Error":                              "/[0]/MNAE/2/Error",
  "2/Holiday/EndDate":                    "/[0]/MNAE/2/Holiday/EndDate",
  "2/Holiday/HolidayState":               "/[0]/MNAE/2/Holiday/HolidayState",
  "2/Holiday/StartDate":                  "/[0]/MNAE/2/Holiday/StartDate",
  "2/UnitIdentifier/Icon":                "/[0]/MNAE/2/UnitIdentifier/Icon",
  "2/UnitIdentifier/Name":                "/[0]/MNAE/2/UnitIdentifier/Name",
  "2/UnitInfo/Manufacturer":              "/[0]/MNAE/2/UnitInfo/Manufacturer",
  "2/UnitInfo/ModelNumber":               "/[0]/MNAE/2/UnitInfo/ModelNumber",
  "2/UnitInfo/SerialNumber":              "/[0]/MNAE/2/UnitInfo/SerialNumber",
  "2/UnitInfo/UnitType":                  "/[0]/MNAE/2/UnitInfo/UnitType",
  "2/UnitInfo/Version/IndoorSettings":    "/[0]/MNAE/2/UnitInfo/Version/IndoorSettings",
  "2/UnitInfo/Version/IndoorSoftware":    "/[0]/MNAE/2/UnitInfo/Version/IndoorSoftware",
  "2/UnitInfo/Version/OutdoorSoftware":   "/[0]/MNAE/2/UnitInfo/Version/OutdoorSoftware",
  "2/UnitInfo/Version/RemoconSettings":   "/[0]/MNAE/2/UnitInfo/Version/RemoconSettings",
  "2/UnitInfo/Version/RemoconSoftware":   "/[0]/MNAE/2/UnitInfo/Version/RemoconSoftware",
  "2/UnitProfile":                        "/[0]/MNAE/2/UnitProfile",
  "2/UnitStatus/WeatherDependentState":   "/[0]/MNAE/2/UnitStatus/WeatherDependentState"
}

####################################################################################################
# Program start
####################################################################################################
#
# Store schedules readed from PROGRAMS file (schedules_set) or from BRP069A62 Daikin LAN Adapter (schedules_get)
#
programs = {}

#
# Log to <stdout> function
#
def do_log(string):
  print(string, flush=True)

#
# Exit logging error msg
#
def exit_error(msg):
    do_log(msg)
    sys.exit(1)

#
# Read filed schedules and load them into a python dictionary variable
#
def read_programs(programs_file):
  global programs
  try:
    with open(programs_file, 'r') as handle:
      programs = ast.literal_eval(handle.read())
  except Exception as e:
    exit_error("!! Exception {}".format(e))

#
# request identifier random generator
#
def randomString(stringLength=5):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

#
# Translate value if translating dictionary is present in item
#
def translate_value(item, value):
  if ("values" in read_items[item]["HA"]):
    return read_items[item]["HA"]["values"][value]
  else:
    if ("values_h" in read_items[item]["HA"]):
      value = json.loads(value)["data"]
      type = "values_h"
      if ("/Cooling/" in value["path"]):
        type = "values_c"
      return(read_items[item]["HA"][type][value["id"]])
  try:
    return(round(float(value)*10)/10)
  except ValueError:
    return value

#
# Update value for sensor in home assistant
#
def do_inform_HA (item, value):
  url = "http://" + cfg['homeassistant']['ip'] + ":"  + str(cfg['homeassistant']['port']) + "/api/states/" + read_items[item]["HA"]["device"]
  headers = {"Authorization": "Bearer " + cfg['homeassistant']['token'], "Content-Type": "application/json"}
  json  = {"state":"%s" % value,  "attributes": read_items[item]["HA"]["attributes"] }
  try:
    conn = requests.post(url,  json = json,  headers = headers)
  except requests.exceptions.RequestException as e:
    do_log("!! Exception {}".format(e))

#
# Get an item value from BRP069A62 (with connected ws)
#
def getValue(ws, endpoint):
   ws.send("{\"m2m:rqp\":{\"op\":2,\"to\":\"" + endpoint + "/la\",\"fr\":\"/HomeAssistant\",\"rqi\":\""
           + randomString() + "\"}}")
   tmp =  json.loads(ws.recv())
   return tmp["m2m:rsp"]["pc"]["m2m:cin"]["con"]

#
#  Write an item value to BRP069A62 (with connected ws)
#
def setValue(ws, endpoint, value):
    ws.send("{\"m2m:rqp\":{\"op\":1,\"to\":\"" + endpoint + "\",\"fr\":\"/HomeAssistant\",\"rqi\":\""
            + randomString() + "\",\"ty\":4,\"pc\":{\"m2m:cin\":{\"con\":"
            + value + ",\"cnf\":\"text/plain:0\"}}}}")
    tmp =  json.loads(ws.recv())
    return (tmp["m2m:rsp"]["rsc"] == 2001)

#
# Build schedule dictionary from string prog
#
def build_program(name, ind, prog):
      programs[name][ind] = {};
      programs[name][ind]["predefined"] = True;
      nam, pred, acts = prog.split("|") 
      programs[name][ind]["name"] = nam
      programs[name][ind]["predefined"] = (pred == "0")
      programs[name][ind]["actions"] = {};
      acts = acts.split(";")
      for wday in range(7):
        programs[name][ind]["actions"][wday] = {}
        for action in range(schedule_items[name]["actions"]):
          it = acts.pop(0)
          tim, tem = it.split(",")
          if (tim != ""):
            programs[name][ind]["actions"][wday][action] = {}
            programs[name][ind]["actions"][wday][action]["h"] = int(tim) // 100
            programs[name][ind]["actions"][wday][action]["m"] = int(tim) % 100
            programs[name][ind]["actions"][wday][action]["t"] = tem
    
#
# Build string from schedule dictionary
#
def build_payload(item):
  payload = "\"{ \\\"data\\\" : ["
  first_program = True
  for prog_n in programs[item]:
    if not first_program:
        payload = payload + ","
    else:
      first_program = False
    payload = payload + "\\\"" + programs[item][prog_n]['name'] + "|"
    if (programs[item][prog_n]['predefined']):
        payload = payload + "0"
    else:
        payload = payload + "1"
    payload = payload + "|"
    first_item = True
    for dayw in programs[item][prog_n]['actions']:
      max_actions = schedule_items[item]['actions']
      for action in range(max_actions):
        if (action in programs[item][prog_n]['actions'][dayw]):
           h = programs[item][prog_n]['actions'][dayw][action]['h']
           m = programs[item][prog_n]['actions'][dayw][action]['m']
           t = programs[item][prog_n]['actions'][dayw][action]['t']
           if not first_item:
               payload = payload + ";"
           else: 
               first_item = False
           payload = payload + "{0:04d},{1}".format(100*h+m, t)
        else:
            if not first_item:
               payload = payload + ";"
    payload = payload + "\\\""
  payload = payload + "]}\""
  return payload

#
# Process set command line arguments
#
def set_function(args):
  if args.item in write_items.keys():
    result = False
    if("values" in write_items[args.item]):
      if(args.value != None):
        if(args.value in write_items[args.item]["values"]):
           type = write_items[args.item]["values"][args.value][0]
           try:
             ws = create_connection("ws://" + cfg["altherma"]["ip"] + "/mca")
             result = setValue(ws, write_items[args.item]["endpoint"],
                                   write_items[args.item]["payload"][type].format(write_items[args.item]["values"][args.value][1]))
           except Exception as e:
             do_log("!! Exception {}".format(e))
             return
           ws.close()
      else:
        print("Allowed values for {}: {}".format(args.item, " ".join(write_items[args.item]["values"].keys())))
        return
    else:
      if(args.value != None):
        try:
          ws = create_connection("ws://" + cfg["altherma"]["ip"] + "/mca")
          result = setValue(ws, write_items[args.item]["endpoint"], args.value)
        except Exception as e:
          do_log("!! Exception {}".format(e))
          return
        ws.close()
      else:
        print("Allowed values for {}: {}".format(args.item, write_items[args.item]["numeric"]))
        return
    print("ok" if result else "ko", end='')
    if (result and args.updateHA):
      do_inform_HA(args.item, args.value)
  else:
    do_log("set: {} invalid endpoint in this mode".format(args.item))

#
# Process get command line arguments
#
def get_function(args):
  if args.item in read_items.keys():
    try:
      ws = create_connection("ws://" + cfg["altherma"]["ip"] + "/mca")
    except Exception as e:
      do_log("!! Exception {}".format(e))
      return
    endpoint = read_items[args.item]["endpoint"]
    try:
      value = translate_value(args.item, getValue(ws, endpoint))
      print (value, end='')
    except Exception as e:
      do_log("Could not get value for {}".format(args.item))
    ws.close()
  else:
      do_log("get: {} invalid endpoint in this mode".format(args.item))

#
# Process sensord command line arguments
#
def sensord_function(args):
  if(args.delay == None):
    if ('config' in cfg) and ('interval' in cfg['config']):
       sleep_time = cfg['config']['interval']
    else:
      sleep_time = DELAY_INT
  else:
    sleep_time = args.delay
  if 'all' in args.item:
    endpoints = read_items
  else:    
    endpoints = []
    for item in args.item:
      if (item in read_items.keys()):
        endpoints.append(item)
      else:
        if item in all_read_items.keys():
          do_log("Invalid endpoint in this mode: {} in sensord command. Please use one of: {}.".format(item, list(read_items.keys())))
        else:
          do_log("Unknown endpoint: {} in sensord command. Please use one of: {}.".format(item, list(read_items.keys())))
    endpoints = list(set(endpoints))

  while True:
    try:
      ws = create_connection("ws://" + cfg["altherma"]["ip"] + "/mca")
    except Exception as e:
      do_log("!! Exception {}".format(e))
      time.sleep(sleep_time)
      continue

    for item in endpoints:
      try:
          value = translate_value(item, getValue(ws, read_items[item]["endpoint"]))
      except Exception as e:
        do_log("Could not get value for {}".format(item))
        continue
      do_inform_HA(item,  value )
      do_log("{}: {}".format(item, value))
    ws.close()
    if(args.once):
      break
    time.sleep(sleep_time)

#
# Process schedule_get command line arguments
#
def schedule_get_function(args):
  if 'all' in args.item:
    endpoints = schedule_read_items
  else:
    endpoints = []
    for item in args.item:
      if (item in schedule_read_items.keys()):
        endpoints.append(item)
      else:
        if item in all_schedule_read_items.keys():
          do_log("Invalid endpoint in this mode: {} in schedule command. Please use one of: {}.".format(item, list(schedule_read_items.keys())))
        else:
          do_log("Unknown endpoint: {} in schedule command. Please use one of: {}.".format(item, list(schedule_read_items.keys())))
    endpoints = list(set(endpoints))
  
  try:
    ws = create_connection("ws://" + cfg["altherma"]["ip"] + "/mca")
  except Exception as e:
    do_log("!! Exception {}".format(e))
    return

  pp = pprint.PrettyPrinter(indent=2)
  for item in endpoints:
    try:
      value = getValue(ws, schedule_read_items[item]["endpoint"])
    except Exception as e:
      do_log("Could not get value for {}".format(item))
      continue
    value = json.loads(value)["data"]
    if type(value) is dict:
      pp.pprint(value)
    else:
      if("programs" in schedule_read_items[item]):
        programs[item] = {}
        for x in value:
           build_program(item, value.index(x), x)
      else:
        pp.pprint(value)
  ws.close()
  if ( len(programs)>0 ):
    pp.pprint(programs)

#
# Process schedule_set command line arguments
#
def schedule_set_function(args):
  result = False
  read_programs(programs_file)
  try:
    ws = create_connection("ws://" + cfg["altherma"]["ip"] + "/mca")
    result = setValue(ws, schedule_items[args.item]["endpoint"], build_payload(args.item))
  except Exception as e:
    do_log("Could not set value for {}".format(item))
    return
  ws.close()
  print("ok" if result else "ko", end='')

####################################################################################################
# Program execution start
####################################################################################################

all_read_items          = { **read_items,          **read_items_rt  }
all_write_items         = { **write_items,         **write_items_rt }
all_schedule_items      = { **schedule_items,      **schedule_items_rt }
all_schedule_read_items = { **schedule_read_items, **schedule_read_items_rt, **schedule_items, **schedule_items_rt }

#
# Parameters processing
#
parser = argparse.ArgumentParser(description='Interface program for Daikin BRP069A62')

parser.add_argument('-c', '--config',   help="Config file",   default=DKNCONFIG)
parser.add_argument('-p', '--programs', help="Programs file")
parser.add_argument('-r', '--rtmode',   help="Use with Altherma in RT mode", action='store_true')

subparsers = parser.add_subparsers(help='Main command option')

parser_get = subparsers.add_parser('get', help='Get a value from DAIKIN Altherma')
parser_get.add_argument('item', type=str, choices=all_read_items.keys(), help="Item to get value from")
parser_get.set_defaults(func=get_function)

parser_set = subparsers.add_parser('set',  help='Set a value into DAIKIN Altherma')
parser_set.add_argument('item', type=str, choices=all_write_items.keys(), help="Item to set value to")
parser_set.add_argument('value', type=str, nargs='?', help="Value to set")
parser_set.add_argument('--updateHA', '-u', action="store_true", help="Update HA")
parser_set.set_defaults(func=set_function)

parser_sd = subparsers.add_parser('sensord',  help='Run as a daemon to get Altherma values and send them to HA')
parser_sd.add_argument('item', type=str, nargs='*', default=['all'], help="Item endpoint to get values from (or 'all')")
parser_sd.add_argument('--delay', '-d', type=int, help="Interval for reading values")
parser_sd.add_argument('--once', action="store_true", help="Run once and exit")
parser_sd.set_defaults(func=sensord_function)

parser_sg = subparsers.add_parser('schedules_get',  help='Get Altherma schedules info')
parser_sg.add_argument('item', type=str, nargs='*', default=['all'], help="Item schedule to get values from (or 'all')")
parser_sg.set_defaults(func=schedule_get_function)

parser_st = subparsers.add_parser('schedules_set',  help='Upload schedules to Altherma')
parser_st.add_argument('item', type=str, choices=all_schedule_items.keys(), help="Item schedule to set values to")
parser_st.add_argument('value', type=str, nargs='?', help="Value to set")
parser_st.set_defaults(func=schedule_set_function)

args = parser.parse_args()

#
# Read config file
#
try:
  with open(args.config, 'r') as ymlfile:
    cfg = yaml.load(ymlfile,  Loader=yaml.SafeLoader)
except:
  exit_error('Cannot open or read config file {}'.format(args.config))

#
# Minimal configuration checking
#

if (not ('homeassistant' in cfg) and not ('ip' in cfg['homeassistant'])
    and not ('port' in  cfg['homeassistant'])
    and not ('token' in  cfg['homeassistant'])):
      exit_error('No homeassistant info found in config file')

if (not ('altherma' in cfg) and not ('ip' in cfg['altherma'])):
      exit_error('No Altherma info found in config file')

if(args.programs == None):
  if (('config' in cfg) and ('programs' in cfg['config'])):
    programs_file = cfg['config']['programs']
  else:
    programs_file = PROGRAMS
else:
    programs_file = args.programs

if( not args.rtmode):
  if ('config' in cfg) and ('mode' in cfg['config']):
     rtmode = cfg['config']['mode'] == 'rt'
  else:
     rtmode = False
else:
  rtmode = True

#
# Update endpoints in RT mode
#
if(rtmode):
   read_items.update(read_items_rt)
   write_items.update(write_items_rt)
   schedule_read_items.update(schedule_read_items_rt)
   schedule_items.update(schedule_items_rt)

schedule_read_items.update(schedule_items)

#
# Execution following command-line options
#
try:
  if('item' in args):
      args.func(args)
  else:
    parser.print_help()
except KeyboardInterrupt:
  do_log("{0}: Exit program".format(time.ctime()))

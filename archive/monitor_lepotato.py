#!/usr/bin/env python
# Markham Lee (C) 2023
# Hardware Monitor for Linux & Windows:
# https://github.com/MarkhamLee/HardwareMonitoring
# This script is for Raspberry Pi 4Bs running Ubuntu, the sensors
# are fairly simple, one temperature sensor for the CPU, nothing SOC
# or GPU specific. Psutil only returns one CPU despite their being four
# cores, meaning, they're all treated as one.
# CLI instructions <filename> <MQTT topic name as a string>
# <sleep interval as an integer>
import gc
import json
import logging
import os
import sys
from time import sleep
from linux_cpu_data import LinuxCpuData

# this allows us to import modules from the parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from common.device_tool import DeviceUtilities  # noqa: E402

# create logger for logging errors, exceptions and the like
logging.basicConfig(filename='hardwareDataLinuxCPU.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(threadName)s\
                        : %(message)s')


def monitor(client: object, get_data: object, TOPIC: str, INTERVAL: int):

    while True:

        # get CPU utilization
        cpu_util = get_data.get_cpu_data()

        # get current RAM use
        ram_use = get_data.get_ram_data()

        # get current freq and core count
        cpu_freq, core_count = get_data.get_freq()

        # get CPU temperature
        cpu_temp = get_data.libre_lepotato_temps()

        payload = {
            "cpuTemp": cpu_temp,
            "cpuFreq": cpu_freq,
            "cpuUse": cpu_util,
            "ramUse": ram_use
        }

        payload = json.dumps(payload)

        result = client.publish(TOPIC, payload)
        status = result[0]

        if status == 0:

            print(f'Failed to send {payload} to: {TOPIC}')
            logging.debug(f'MQTT publishing failure, return code: {status}')

        del payload, cpu_util, ram_use, cpu_freq, cpu_temp, status, result
        gc.collect()

        sleep(INTERVAL)


def main():

    # instantiate utilities class
    device_utilities = DeviceUtilities()

    # parse command line arguments
    args = sys.argv[1:]

    TOPIC = args[0]
    INTERVAL = args[1]

    # load environmental variables
    MQTT_BROKER = os.environ["MQTT_BROKER"]
    MQTT_USER = os.environ['MQTT_USER']
    MQTT_SECRET = os.environ['MQTT_SECRET']
    MQTT_PORT = int(os.environ['MQTT_PORT'])

    # get unique client ID
    clientID = device_utilities.getClientID()

    # get mqtt client
    client, code = device_utilities.mqttClient(clientID, MQTT_USER,
                                               MQTT_SECRET, MQTT_BROKER,
                                               MQTT_PORT)

    # instantiate CPU data class & utilities class
    get_data = LinuxCpuData()

    # start monitoring
    try:
        monitor(client, get_data, TOPIC, INTERVAL)

    finally:
        client.loop_stop()


if __name__ == '__main__':
    main()
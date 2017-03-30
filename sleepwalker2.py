#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import subprocess
from time import sleep

timeout = 5.0
sleeping = False

while True:
    idle = float(subprocess.check_output(["./xidle"]))

    print("Idle for %s seconds..." % idle)

    if idle <= timeout: # if idle for n-seconds...
        if sleeping == True:
            print("Waking visible windows up...")

            sleeping = False
    else:
        if sleeping == False:
            print("Putting windows to sleep...")

            sleeping = True

    sleep(0.25)

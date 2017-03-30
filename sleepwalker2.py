#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import subprocess
from time import sleep

timeout = 5.0
sleeping = False

while True:
    idle = float(subprocess.check_output(["./xidle"]))

    print("Idle for %s seconds..." % idle)

    if idle <= timeout: # if n-seconds idle...
        if sleeping == True:
            print("Waking all visible windows up...")

            sleeping = False
    else:
        if sleeping == False:
            print("Putting all windows to sleep...")

            sleeping = True

    sleep(0.25)

#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import subprocess
import ewmh
from time import sleep

def get_idle_time():
    idle = float(subprocess.check_output(["./xidle"]))

    return idle

'''
def get_all_window_ids():
    pass

def get_visible_window_ids():
    pass
'''

def wakeup_windows(window_list=None):
    print("Waking windows up...")

    pids = [1678]

    for pid in pids:
        print("subprocess.call([\"kill\"], [\"-SIGCONT\"], [%s])" % pid)

def sleep_windows(window_list=None):
    print("Putting windows to sleep...")

    pids = [1678]

    for pid in pids:
        print("subprocess.call([\"kill\"], [\"-SIGSTOP\"], [%s])" % pid)

if __name__ == "__main__":
    timeout = 2.0
    sleeping = False

    while True:
        idle = get_idle_time()

        print("Idle for %s seconds..." % idle)

        if idle >= timeout: # if n-seconds idle...
            if sleeping == False:
                sleep_windows()

                sleeping = True
        else:
            if sleeping == True:
                wakeup_windows()

                sleeping = False

        sleep(0.25)

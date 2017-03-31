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

    pids = set()

    for wid in ewmh.getClientList():
        pid = int(ewmh.getWmPid(wid))

        pids.add(pid)

    for pid in pids:
        print("Wake up process with pid %s..." % pid)

        subprocess.call(["kill", "-SIGCONT", str(pid)])

def sleep_windows(window_list=None):
    print("Putting windows to sleep...")

    active_window = ewmh.getActiveWindow()
    active_window_pid = ewmh.getWmPid(active_window)

    pids = set()

    for wid in ewmh.getClientList():
        pid = int(ewmh.getWmPid(wid))

        if pid == active_window_pid:
            continue
        else:
            pids.add(pid)

    for pid in pids:
        print("Put process to sleep with pid %s..." % pid)

        subprocess.call(["kill", "-SIGSTOP", str(pid)])

if __name__ == "__main__":
    timeout = 2.0
    sleeping = False

    ewmh = ewmh.EWMH()

    while True:
        idle = get_idle_time()

        if idle >= timeout: # if n-seconds idle...
            if sleeping == False:
                sleep_windows()

                sleeping = True
        else:
            print("Idle for %s seconds..." % idle)

            if sleeping == True:
                wakeup_windows()

                sleeping = False

        sleep(0.25)

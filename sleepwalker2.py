#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import subprocess
import ewmh
from time import sleep

def get_idle_time():
    idle = float(subprocess.check_output(["./xidle"]))

    return idle

def get_cmdline(pid):
    cmdline = open("/proc/" + str(pid) + "/cmdline").read().split("\0")[0]

    return cmdline

def get_pids():
    pids = set()

    for wid in ewmh.getClientList():
        pid = int(ewmh.getWmPid(wid))

        pids.add(pid)

    return pids

def wakeup_windows():
    print("Waking windows up...")

    pids = get_pids()

    for pid in pids:
        cmdline = get_cmdline(pid)

        print("Wake up process with pid %s (%s)..." % (pid, cmdline))

        subprocess.call(["kill", "-SIGCONT", str(pid)])

    global sleeping

    sleeping = False

def sleep_windows():
    print("Putting windows to sleep...")

    pids = get_pids()

    for pid in pids:
        cmdline = get_cmdline(pid)

        print("Put process to sleep with pid %s (%s)..." % (pid, cmdline))

        subprocess.call(["kill", "-SIGSTOP", str(pid)])

    global sleeping

    sleeping = True

if __name__ == "__main__":
    timeout = 2.0
    sleeping = False

    ewmh = ewmh.EWMH()

    while True:
        idle = get_idle_time()

        if idle >= timeout: # if idle for n-seconds...
            if sleeping == False:
                sleep_windows()
        else:
            print("Idle for %s seconds..." % idle)

            if sleeping == True:
                wakeup_windows()

        sleep(0.25)

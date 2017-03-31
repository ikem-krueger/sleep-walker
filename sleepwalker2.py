#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import subprocess
import ewmh
from time import sleep

def get_idle_time():
    idle = float(subprocess.check_output(["./xidle"]))

    return idle

def get_exe(pid):
    exe = subprocess.check_output(["readlink", "/proc/" + str(pid) + "/exe"]).strip()

    return exe

def get_pids():
    pids = set()

    for wid in ewmh.getClientList():
        pid = int(ewmh.getWmPid(wid))
        exe = get_exe(pid)

        if exe == "/usr/bin/mate-terminal":
            print("Filter %s..." % exe)

            continue

        pids.add(pid)

    return pids

def wakeup_windows():
    print("Waking windows up...")

    pids = get_pids()

    for pid in pids:
        exe = get_exe(pid)

        print("Wake up process with pid %s (%s)..." % (pid, exe))

        subprocess.call(["kill", "-SIGCONT", str(pid)])

    global sleeping

    sleeping = False

def sleep_windows():
    print("Putting windows to sleep...")

    pids = get_pids()

    for pid in pids:
        exe = get_exe(pid)

        print("Put process to sleep with pid %s (%s)..." % (pid, exe))

        subprocess.call(["kill", "-SIGSTOP", str(pid)])

    global sleeping

    sleeping = True

if __name__ == "__main__":
    timeout = 5.0
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

        sleep(0.2)

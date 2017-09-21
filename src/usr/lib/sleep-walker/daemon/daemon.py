# /usr/bin/env python2
# -*- coding: utf-8 -*-
#  
#  Copyright 2017 Ikem Krueger <ikem.krueger@gmail.com>
#  
#  This file is part of sleep-walker.
#  
#  sleep-walker is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#  
#  You should have received a copy of the GNU Affero General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.
#  
#  

from xcovered import *
from xidle import get_idle_time
from time import sleep

import signal
import ctypes
import subprocess
import os
import sys

def sigterm_handler(signal, frame):
    wake_windows_up()

    sys.exit(0)

def load_whitelist():
    whitelist = set()

    for whitelist_file in [system_whitelist, user_whitelist]:
        if os.path.exists(whitelist_file):
            whitelist = whitelist.union(open(whitelist_file).read().split())
            
    return whitelist

def get_all_windows():
    window_list = ewmh.getClientList()

    return window_list

def get_window_pid(window_id):
    pid = ewmh.getWmPid(window_id)

    return pid

def get_window_command(window_id):
    pid = get_window_pid(window_id)
    
    command = get_pid_command(pid)
    
    return command

def get_pid_command(pid):
    pid_uid = os.stat("/proc/%s" % pid).st_uid
    
    if pid_uid == uid:
        exe = os.readlink("/proc/%s/exe" % pid)
        command = exe.split("/")[-1].split()[0]
    else:
        command = None

    return command

def get_all_pids():
    window_list = get_all_windows()
    pids = []
    
    for window_id in window_list:
        pid = get_window_pid(window_id)
        
        pids.append(pid)
    
    return pids

def get_whitelist_pids(pids, whitelist):
    pids_ = []
    
    for pid in pids:
        command = get_pid_command(pid)
        
        if command in whitelist:
            pids_.append(pid)
            
    return pids_

def get_audio_pids():
    pids = []

    output = subprocess.check_output(["pacmd", "list-sink-inputs"])

    for line in output.split("\n"):
        line = line.strip()

        if line.startswith("application.process.id"):
            pid = int(line.split(" = ")[1].strip('"'))

            pids.append(pid)

    return pids

def get_active_pids():
    pids = []
    
    active_window_id = ewmh.getActiveWindow()
    pid = get_window_pid(active_window_id)
    
    pids.append(pid)
    
    return pids

def put_pids_to_sleep(pids):
    for pid in pids:
        pid_uid = os.stat("/proc/%s" % pid).st_uid
        
        if pid_uid == uid:
            os.kill(pid, signal.SIGSTOP)

def wake_pids_up(pids):
    for pid in pids:
        pid_uid = os.stat("/proc/%s" % pid).st_uid
        
        if pid_uid == uid:
            os.kill(pid, signal.SIGCONT)

def is_on_current_desktop(window_id):
    window_desktop = ewmh.getWmDesktop(window_id)
    current_desktop = ewmh.getCurrentDesktop()
    
    return window_desktop == current_desktop

def is_active(window_id):
    active_window_id = ewmh.getActiveWindow()
    
    return window_id == active_window_id

def is_minimized(window_id):
    window_state = ewmh.getWmState(window_id, True)
    
    return '_NET_WM_STATE_HIDDEN' in window_state

def is_playing_audio(window_id):
    pid = get_window_pid(window_id)
    audio_pids = get_audio_pids()
    
    return pid in audio_pids

def foo(window_id):
    sleep_pids = set()

    window_name = ewmh.getWmName(window_id)
    pid = get_window_pid(window_id)
    command = get_window_command(window_id)
    
    if is_on_current_desktop(window_id):
        if is_minimized(window_id):
            print("Window %s %s %s %s--> minimzed --> sleep" % (window_id, pid, command, window_name))

            sleep_pids.add(pid)
        else:
            if is_fully_covered(window_id):
                print("Window %s %s %s %s --> fully covered --> sleep" % (window_id, pid, command, window_name))

                sleep_pids.add(pid)
    else:
        print("Window %s %s %s %s --> on other desktop --> sleep" % (window_id, pid, command, window_name))

        sleep_pids.add(pid)

    return sleep_pids

def put_windows_to_sleep():
    window_list_all = get_all_windows()
    sleep_pids = set()

    for window_id in window_list_all:
        bla = foo(window_id)
        
        sleep_pids.update(bla)

    whitelist_pids = set(get_whitelist_pids(sleep_pids, whitelist) + get_audio_pids() + get_active_pids())
    sleep_pids = sleep_pids - whitelist_pids

    print("Skip: %s" % whitelist_pids)
    print("Sleep: %s" % sleep_pids)

    put_pids_to_sleep(sleep_pids)
    wake_pids_up(get_active_pids())

def wake_windows_up():
    pids = get_all_pids()
    
    wake_pids_up(pids)

def main():
    wake_windows_up()

    sleeping = False

    while True:
        idle = get_idle_time(xlib, dpy, root, xss)

        if idle >= timeout: # if idle for n-seconds...
            if not sleeping:
                put_windows_to_sleep()

                sleeping = True
        else:
            print("Idle for %s seconds..." % idle)

            if sleeping:
                wake_windows_up()

                sleeping = False

        sleep(0.25)

if __name__ == "__main__":
    uid = os.getuid()
    home = os.getenv("HOME")
    
    system_whitelist = "/etc/sleep-walker/whitelist"
    user_whitelist = "%s/.sleep-walker/whitelist" % home
    
    # get_idle_time(xlib, dpy, root, xss)
    xlib = ctypes.cdll.LoadLibrary('libX11.so')
    dpy = xlib.XOpenDisplay(os.environ['DISPLAY'])

    root = xlib.XDefaultRootWindow(dpy)
    xss = ctypes.cdll.LoadLibrary('libXss.so.1')

    timeout = 5.0 # debug: need to find the sweet spot...
    notifications = True

    whitelist = load_whitelist()

    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)
    #signal.signal(signal.SIGUSR1, sigusr1_handler)

    main()

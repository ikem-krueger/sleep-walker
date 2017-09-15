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

import ewmh
import xcovered
import os
import signal
import sys
import subprocess

#from xidle import get_idle_time
from Xlib import X

def sigterm_handler(signal, frame):
    wake_windows_up()

    sys.exit(0)

def load_whitelist():
    whitelist = set()

    for whitelist_file in [system_whitelist, user_whitelist]:
        if os.path.exists(whitelist_file):
            whitelist = whitelist.union(open(whitelist_file).read().split())
            
    return whitelist

def get_window_command(window_id):
    pid = ewmh.getWmPid(window_id)
    
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
    pids = []
    
    for window_id in ewmh.getClientList():
        pid = ewmh.getWmPid(window_id)
        
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
    pid = ewmh.getWmPid(active_window_id)
    
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
    window_state = ewmh.getWmState(window_id)
    
    return '_NET_WM_STATE_HIDDEN' in window_state

def is_playing_audio(window_id):
    pid = ewmh.getWmPid(window_id)
    audio_pids = get_audio_pids()
    
    return pid in audio_pids

def put_windows_to_sleep():
    sleep_pids = set()

    for window_id in ewmh.getClientList():
        window_name = ewmh.getWmName(window_id)
        pid = ewmh.getWmPid(window_id)
        command = get_window_command(window_id)
        
        '''
        if is_on_current_desktop(window_id):
            if is_minimized(window_id):
                print("Window %s %s %s %s--> minimzed --> sleep" % (window_id, pid, command, window_name))

                sleep_pids.add(pid)
            else xc.is_fully_covered(window_id):
        '''
        if is_on_current_desktop(window_id):
            if xc.is_fully_covered(window_id):
                print("Window %s %s %s %s --> fully covered --> sleep" % (window_id, pid, command, window_name))

                sleep_pids.add(pid)
        else:
            print("Window %s %s %s %s --> on other desktop --> sleep" % (window_id, pid, command, window_name))

            sleep_pids.add(pid)

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

    ewmh.root.change_attributes(event_mask=X.PropertyChangeMask)
    
    NET_ACTIVE_WINDOW = 344

    old_active_window = ewmh.getActiveWindow()

    while True:
        ev = ewmh.dpy.next_event()        

        if ev.type == X.PropertyNotify and \
           ev.state == X.PropertyNewValue and \
           ev.atom == NET_ACTIVE_WINDOW:
                active_window = ewmh.getActiveWindow()
                
                if active_window != old_active_window:
                    put_windows_to_sleep()

                    old_active_window = active_window

if __name__ == "__main__":
    ewmh = ewmh.EWMH()
    xc = xcovered.XCovered(ewmh)

    uid = os.getuid()
    home = os.getenv("HOME")
    
    system_whitelist = "/etc/sleep-walker/whitelist"
    user_whitelist = "%s/.sleep-walker/whitelist" % home
    
    notifications = True

    whitelist = load_whitelist()

    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)
    #signal.signal(signal.SIGUSR1, sigusr1_handler)

    main()


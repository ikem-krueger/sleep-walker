#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from ewmh import EWMH
from time import sleep

ewmh = EWMH() # Extended Window Manager Hints

'''
ActiveWindow = ewmh.getActiveWindow()
ClientList = ewmh.getClientList()
ClientListStacking = ewmh.getClientListStacking()
CurrentDesktop = ewmh.getCurrentDesktop()
NumberOfDesktops = ewmh.getNumberOfDesktops()
Property = ewmh.getProperty()
WmDesktop = ewmh.getWmDesktop()
WmName = ewmh.getWmName()
WmPid = getWmPid()
WmState = getWmState()
'''

desktop = ewmh.getCurrentDesktop() + 1

sleep(1)

print("Desktop Id|Active|Window Title|State|Process Id")

for i, window_id in enumerate(ewmh.getClientList()):
    desktop_number = ewmh.getWmDesktop(window_id) + 1
    window_title = ewmh.getWmName(window_id)
    process_id = ewmh.getWmPid(window_id)
    state = ewmh.getWmState(window_id)

    active_window = ewmh.getActiveWindow()
    
    if window_id == active_window:
        active = "* "
    else:
        active = "  "

    if desktop_number == desktop:
        print("%s %s|%s|%s|%s" % (desktop_number, active, window_title, state, process_id))

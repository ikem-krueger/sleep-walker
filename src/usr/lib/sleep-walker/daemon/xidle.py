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

import ctypes
import os

class XScreenSaverInfo(ctypes.Structure):
  """ typedef struct { ... } XScreenSaverInfo; """
  _fields_ = [('window',      ctypes.c_ulong), # screen saver window
              ('state',       ctypes.c_int),   # off,on,disabled
              ('kind',        ctypes.c_int),   # blanked,internal,external
              ('since',       ctypes.c_ulong), # milliseconds
              ('idle',        ctypes.c_ulong), # milliseconds
              ('event_mask',  ctypes.c_ulong)] # events

#@profile
def get_idle_time(xlib, dpy, root, xss):
    xss.XScreenSaverAllocInfo.restype = ctypes.POINTER(XScreenSaverInfo)
    xss_info = xss.XScreenSaverAllocInfo()
    xss.XScreenSaverQueryInfo(dpy, root, xss_info)

    idle = float(xss_info.contents.idle) / 1000

    # Cleaning Up
    #xss.XFree(xss_info)
    #xss.XCloseDisplay(dpy)

    return idle

if __name__ == "__main__":
    xlib = ctypes.cdll.LoadLibrary('libX11.so')
    dpy = xlib.XOpenDisplay(os.environ['DISPLAY'])

    root = xlib.XDefaultRootWindow(dpy)
    xss = ctypes.cdll.LoadLibrary('libXss.so')

    idle = get_idle_time(xlib, dpy, root, xss)

    print("%s" % idle)

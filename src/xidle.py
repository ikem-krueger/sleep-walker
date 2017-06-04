import Xlib.display
display = Xlib.display.Display()
focus = display.get_input_focus()
print "WM Class: %s" % ( focus.focus.get_wm_class(), )
print "WM Name: %s" % ( focus.focus.get_wm_name(), )
X11 Idle Time using the XScreenSaver extension
import ctypes
import os
http://thp.io/2007/09/x11-idle-time-and-focused-window-in.html
http://www.freedesktop.org/software/ConsoleKit/doc/ConsoleKit.html#Session:idle-hint

class XScreenSaverInfo( ctypes.Structure):
  """ typedef struct { ... } XScreenSaverInfo; """
  _fields_ = [('window',      ctypes.c_ulong), # screen saver window
              ('state',       ctypes.c_int),   # off,on,disabled
              ('kind',        ctypes.c_int),   # blanked,internal,external
              ('since',       ctypes.c_ulong), # milliseconds
              ('idle',        ctypes.c_ulong), # milliseconds
              ('event_mask',  ctypes.c_ulong)] # events

xlib = ctypes.cdll.LoadLibrary( 'libX11.so')
dpy = xlib.XOpenDisplay( os.environ['DISPLAY'])
root = xlib.XDefaultRootWindow( dpy)
xss = ctypes.cdll.LoadLibrary( 'libXss.so')
xss.XScreenSaverAllocInfo.restype = ctypes.POINTER(XScreenSaverInfo)
xss_info = xss.XScreenSaverAllocInfo()
xss.XScreenSaverQueryInfo( dpy, root, xss_info)
print "Idle time in milliseconds: %d" % ( xss_info.contents.idle, )
If
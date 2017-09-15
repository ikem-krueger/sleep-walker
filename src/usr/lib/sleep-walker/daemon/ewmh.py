#!/usr/bin/env python

from Xlib import X, display, protocol, error
import sys

# This class is based on code from the pyewmh project. The library itself is not
# being used directly because it is not packaged in Debian and we, the
# BunsenLabs authors, want to stay as close to vanilla Debian as possible. Below
# follows an excerpt from pyewmh's documentation.
class EWMH(object):
    """This module intends to provide an implementation of Extended Window Manager Hints, based on
    the Xlib modules for python. It provides the ability to get and set properties defined by the
    EWMH spec.

    :param _dpy: the display to use. If not given, Xlib.display.Display() is used."""

    def __init__(self, _dpy=None):
        self.dpy = _dpy or display.Display()
        self.root = self.dpy.screen().root

    def _get_property(self, win, prop):
        """Gets an X Window's property, or None."""
        atom = win.get_full_property(self.dpy.intern_atom(prop), X.AnyPropertyType)
        if atom:
            return atom.value
        return None

    def _set_property(self, win, prop, data, mask=None):
        """Sends a ClientMessage event to an X Window."""
        if isinstance(data, str):
            datasize = 8
        else:
            data = (data+[0]*(5-len(data)))[:5]
            datasize = 32

        event = protocol.event.ClientMessage(window=win,
                                             client_type=self.dpy.intern_atom(prop),
                                             data=(datasize, data))

        if not mask:
            mask = (X.SubstructureRedirectMask|X.SubstructureNotifyMask)
        self.root.send_event(event, event_mask=mask)
        self.dpy.flush()

    def getClientList(self):
        windows = self._get_property(self.root, '_NET_CLIENT_LIST')
        return [self.dpy.create_resource_object('window', window) for window in windows]

    def getClientListStacking(self):
        windows = self._get_property(self.root, '_NET_CLIENT_LIST_STACKING')
        return [self.dpy.create_resource_object('window', window) for window in windows]

    def getActiveWindow(self):
        """Returns the currently active window, or None. (property _NET_ACTIVE_WINDOW)"""
        window = self._get_property(self.root, '_NET_ACTIVE_WINDOW')
        if window:
            return self.dpy.create_resource_object('window', window[0])
        return None

    def getCurrentDesktop(self):
        desktop = self._get_property(self.root, '_NET_CURRENT_DESKTOP')
        return desktop

    def getWorkarea(self):
        """Returns the work area, which is the size of the screen minus panels and docks and the like."""
        workarea = self._get_property(self.root, '_NET_WORKAREA')
        return workarea[0], workarea[1], workarea[2], workarea[3]

    def getFrameExtents(self, win):
        """Returns the frame extents of the window's frame.

        :param win: the X Window object whose frame to retrieve"""
        extents = self._get_property(win, '_NET_FRAME_EXTENTS')
        if extents:
            return extents[0], extents[1], extents[2], extents[3]
        return 0, 0, 0, 0

    def getWmDesktop(self, win):
        desktop = self._get_property(win, '_NET_WM_DESKTOP')
        return desktop

    def getWmName(self, win):
        name = self._get_property(win, '_NET_WM_NAME')
        return name

    def getWmPid(self, win):
        """Returns the PID of the process owning the X Window, or 0. (property _NET_WM_PID)

        :param win: the X Window object whose owning proces' PID to retrieve"""
        prop = self._get_property(win, '_NET_WM_PID')
        if prop:
            return prop[0]
        return 0

    def getWmState(self, win):
        state = self._get_property(win, '_NET_WM_STATE')
        return state

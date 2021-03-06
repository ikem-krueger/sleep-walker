#!/usr/bin/env python

"""bl-aerosnap intends to add aero style window snapping to Openbox, or any
somewhat EWMH-compliant, reparenting window manager. The EWMH hints required
for proper operation are:
    * _NET_ACTIVE_WINDOW
    * _NET_WM_PID
    * _NET_WM_STATE
      * _NET_WM_STATE_MAXIMIZED
      * _NET_WM_STATE_MAXIMIZED_VERT
      * _NET_WM_STATE_MAXIMIZED_HORZ
    * _NET_MOVERESIZE_WINDOW
    * _NET_WORKAREA
    * _NET_FRAME_EXTENTS

bl-aerosnap was originally written for CrunchBang Linux <http://crunchbang.org/>
by Philip Newborough <corenominal@corenominal.org>. It is repackaged for
BunsenLabs by John Crawley and rewritten for BunsenLabs to use Xlib/EWMH instead
of subprocesses by Jente Hidskes <hjdskes@gmail.com>."""

# TODO:
# 1. windows with an originally negative position will not be able to be
#    restored, see https://gist.github.com/Unia/df288b42c2d60504256b1674af810749
#    for a traceback.

from Xlib import X, display, protocol
import argparse, os, sys, tempfile

# A dict mapping window IDs (see get_window_id below) to that window's geometry
# and snap direction, if any.
WINDOWS = {}

# TODO(Python3): replace with an actual enum.
class Snap(object):
    """This class is here to mimic an enum, which is absent in python 2."""
    Left, Right, Top, Bottom = range(4)

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
        self.dpy.screen().root.send_event(event, event_mask=mask)
        self.dpy.flush()

    def set_window_state(self, win, action, state, state2=0):
        """Sets or unsets one or two state(s) for the given window. (property _NEW_WM_STATE)

        :param win: the X Window object whose state to set
        :param action: 0 to remove, 1 to add or 2 to toggle state(s)
        :param state: a state
        :type state: int or str (see the EWMH spec)
        :param state2: a state or 0
        :type state2: int or str (see the EWMH spec)"""
        if isinstance(state, int) is False:
            state = self.dpy.intern_atom(state, 1)
        if isinstance(state2, int) is False:
            state2 = self.dpy.intern_atom(state2, 1)
        self._set_property(win, '_NET_WM_STATE', [action, state, state2, 1])

    def set_move_resize_window(self, win, gravity=0, x=None, y=None, width=None, height=None):
        """Set the property _NET_MOVERESIZE_WINDOW to move or resize the given window.
        Flags are automatically calculated if x, y, w or h are defined.

        :param win: the X Window object to move and resize
        :param gravity: gravity (one of the Xlib.X.*Gravity constant or 0)
        :param x: int or None
        :param y: int or None
        :param w: int or None
        :param h: int or None"""
        gravity_flags = gravity | 0b0000100000000000 # indicate source (application)
        if x is None:
            x = 0
        else:
            gravity_flags = gravity_flags | 0b0000010000000000 # indicate presence of x
        if y is None:
            y = 0
        else:
            gravity_flags = gravity_flags | 0b0000001000000000 # indicate presence of y
        if width is None:
            width = 0
        else:
            gravity_flags = gravity_flags | 0b0000000100000000 # indicate presence of w
        if height is None:
            height = 0
        else:
            gravity_flags = gravity_flags | 0b0000000010000000 # indicate presence of h
        self._set_property(win, '_NET_MOVERESIZE_WINDOW',
                           [gravity_flags, int(x), int(y), int(width), int(height)])

    def get_active_window(self):
        """Returns the currently active window, or None. (property _NET_ACTIVE_WINDOW)"""
        window = self._get_property(self.dpy.screen().root, '_NET_ACTIVE_WINDOW')
        if window is None:
            return None
        return self.dpy.create_resource_object('window', window[0])

    def get_window_pid(self, win):
        """Returns the PID of the process owning the X Window, or 0. (property _NET_WM_PID)

        :param win: the X Window object whose owning proces' PID to retrieve"""
        prop = self._get_property(win, '_NET_WM_PID')
        if prop:
            return prop[0]
        return 0

    def get_viewport(self):
        """Returns the viewport, which is the x and y coordinates of the top
        left corner of each desktop."""
        viewport = self._get_property(self.dpy.screen().root, '_NET_DESKTOP_VIEWPORT')
        return viewport[0], viewport[1]

    def get_workarea(self):
        """Returns the work area, which is the size of the screen minus panels and docks and the like."""
        workarea = self._get_property(self.dpy.screen().root, '_NET_WORKAREA')
        return workarea[0], workarea[1], workarea[2], workarea[3]

    def get_frame_extents(self, win):
        """Returns the frame extents of the window's frame.

        :param win: the X Window object whose frame to retrieve"""
        extents = self._get_property(win, '_NET_FRAME_EXTENTS')
        return extents[0], extents[1], extents[2], extents[3]

def write_history(history):
    """Writes the WINDOWS dictionary to history.

    :param history: the file path to write to"""
    with open(history, 'w') as hist_file:
        hist_file.write(str(WINDOWS))

def load_history(history):
    """Loads the history file into the WINDOWS dictionary.

    :param history: the file path to read"""
    if os.path.exists(history) == False:
        return

    with open(history, 'r') as hist_file:
        global WINDOWS
        WINDOWS = eval(hist_file.read())

def window_restore(ewmh, win):
    """Restores the passed-in window's geometry from the WINDOWS dictionary.

    :param ewmh: the :class:`EWMH` module to restore the window
    :param win: the X Window object whose geometry to restore"""
    win_id = get_window_id(ewmh, win)
    geom = WINDOWS[win_id]
    del WINDOWS[win_id]

    ewmh.set_window_state(win, 0, '_NET_WM_STATE_MAXIMIZED_VERT')
    ewmh.set_window_state(win, 0, '_NET_WM_STATE_MAXIMIZED_HORZ')
    ewmh.set_move_resize_window(win, x=geom[0], y=geom[1], width=geom[2], height=geom[3])

    print ("Restoring to: " + str(geom[0]) + ' ' + str(geom[1]) + ' ' + str(geom[2]) + ' ' + str(geom[3]))

def window_snap(ewmh, win, snap):
    """Snaps a window to a position on the screen.

    :param ewmh: the :class:`EWMH` module to snap the window
    :param win: the X Window object to snap
    :param snap: the :class:`Snap` value, deciding which direction to snap to"""
    x, y, width, height = ewmh.get_workarea()
    frame_left, frame_right, frame_top, frame_bottom = ewmh.get_frame_extents(win)

    geom = get_window_geometry(win)
    print ("Snapping window from: " + str(geom[0]) + ' ' + str(geom[1]) + ' ' + str(geom[2]) + ' ' + str(geom[3]))
    ewmh.set_window_state(win, 0, '_NET_WM_STATE_MAXIMIZED_VERT')
    ewmh.set_window_state(win, 0, '_NET_WM_STATE_MAXIMIZED_HORZ')
    ewmh.set_window_state(win, 0, '_NET_WM_STATE_MAXIMIZED')

    # TODO(Python3): replace with switch.
    if snap is Snap.Left:
        print ("Snapping window to: x: " + str(x) + " width: " + str(width / 2 - frame_left - frame_right))
        ewmh.set_window_state(win, 1, '_NET_WM_STATE_MAXIMIZED_VERT')
        ewmh.set_window_state(win, 0, '_NET_WM_STATE_MAXIMIZED_HORZ')
        ewmh.set_move_resize_window(win, x=x, width=width / 2 - frame_left - frame_right)
    elif snap is Snap.Right:
        viewport_x, viewport_y = ewmh.get_viewport()
        offset_x = x - viewport_x
        print ("Snapping window to: x: " + str(width / 2 + offset_x) + ' width: ' + str(width / 2 - frame_left - frame_right))
        ewmh.set_window_state(win, 1, '_NET_WM_STATE_MAXIMIZED_VERT')
        ewmh.set_window_state(win, 0, '_NET_WM_STATE_MAXIMIZED_HORZ')
        ewmh.set_move_resize_window(win, x=width / 2 + offset_x, width=width / 2 - frame_left - frame_right)
    elif snap is Snap.Top:
        print ("Snapping window to: y: " + str(y) + " height: " + str(height / 2 - frame_top - frame_bottom))
        ewmh.set_window_state(win, 0, '_NET_WM_STATE_MAXIMIZED_VERT')
        ewmh.set_window_state(win, 1, '_NET_WM_STATE_MAXIMIZED_HORZ')
        ewmh.set_move_resize_window(win, y=y, height=height / 2 - frame_top - frame_bottom)
    elif snap is Snap.Bottom:
        viewport_x, viewport_y = ewmh.get_viewport()
        offset_y = y - viewport_y
        print ("Snapping window to: y: " +  str(height / 2 + offset_y) + 'height: ' + str(height / 2 - frame_top - frame_bottom))
        ewmh.set_window_state(win, 0, '_NET_WM_STATE_MAXIMIZED_VERT')
        ewmh.set_window_state(win, 1, '_NET_WM_STATE_MAXIMIZED_HORZ')
        ewmh.set_move_resize_window(win, y=height / 2 + offset_y, height=height / 2 - frame_top - frame_bottom)

def get_window_geometry(win):
    """Returns a list containing the window's x, y, width and height coordinates in that order.

    :param win: the X Window object"""
    window_geom = win.get_geometry()
    parent_geom = win.query_tree().parent.get_geometry()
    if parent_geom.x < 0:
        sys.stderr.write("Warning: cannot restore to negative x-coordinate, setting to 0\n")
        parent_geom.x = 0
    if parent_geom.y < 0:
        sys.stderr.write("Warning: cannot restore to negative y-coordinate, setting to 0\n")
        parent_geom.y = 0
    return [parent_geom.x, parent_geom.y, window_geom.width, window_geom.height]

def get_window_id(ewmh, win):
    """Returns a unique identifier for an X Window, made up of its "to string" and process' PID.

    :param ewmh: the :class:`EWMH` class to retrieve the X Window's process' PID
    :param win: the X Window object whose identifier to return"""
    pid = ewmh.get_window_pid(win)
    return str(win) + "-" + str(pid)

def convert(opts):
   """Converts the options into the correct enumeration value.

   :param opts: the options resulting from `ap.parse_args`"""
   if opts.left:
       return Snap.Left
   elif opts.right:
       return Snap.Right
   elif opts.top:
       return Snap.Top
   elif opts.bottom:
       return Snap.Bottom
   raise ValueError("Argument must be one of `--left`, `--right`, `--top` or `--bottom`")

def parse_args(argv):
    """Parses the command line arguments using argparse."""
    ap = argparse.ArgumentParser(description="Add aero style window snapping to " \
            "Openbox, or any EWMH compliant, reparenting window manager")
    ap.add_argument("-l", "--left",
            help="attempt to snap the active window to the left of the screen",
            action="store_true")
    ap.add_argument("-r", "--right",
            help="attempt to snap the active window to the right of the screen",
            action="store_true")
    ap.add_argument("-t", "--top",
            help="attempt to snap the active window to the top of the screen",
            action="store_true")
    ap.add_argument("-b", "--bottom",
            help="attempt to snap the active window to the bottom of the screen",
            action="store_true")
    return ap.parse_args(argv)

def main():
    opts = parse_args(sys.argv[1:])

    dpy = display.Display()
    ewmh = EWMH(dpy)
    active_win = ewmh.get_active_window()

    if dpy.screen().root == active_win:
        sys.exit(0)

    history = tempfile.gettempdir() + '/bl-aerosnap-' + str(os.getuid())
    load_history(history)

    snap = convert(opts)
    wid = get_window_id(ewmh, active_win)
    if wid in WINDOWS:
        # The snap direction is the same; restore the window.
        if snap == WINDOWS[wid][4]:
            window_restore(ewmh, active_win)
        # The snap direction is new; overwrite the remembered snap direction and snap to it.
        else:
            WINDOWS[wid][4] = snap
            window_snap(ewmh, active_win, snap)
    else:
        WINDOWS[wid] = get_window_geometry(active_win) + [snap]
        window_snap(ewmh, active_win, snap)

    write_history(history)

if __name__ == "__main__":
    main()

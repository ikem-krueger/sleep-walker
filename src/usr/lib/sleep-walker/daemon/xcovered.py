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
# Find out if C is completely or only partially covered by A or B
#
#  +-----------+
#  |   +===+   |
#  |   | +-------+
#  | C | |   B   |
#  |   | +-------+
#  +---| A |---+
#      +---+
#
# @return 0 if window ist not visible, 1 if visible
#
# Note: Only tested with three windows like in sketch above, but
#     it should also work for an arbitrary amount of overlapping windows

from Xlib import X, Xatom
import sys
import ewmh

def get_window_id(window_id):
    # BUG: this only works on the desktop...
    #window_id = str(window_id).split(">")[1].strip("()")
    window_id = str(window_id).split("(")[1].strip(")")
    
    return window_id

def overlap(x1,y1,w1,h1, x2,y2,w2,h2, x3=0,y3=0,w3=65535,h3=65535):
    # Calculates the area of the union of all overlapping areas. If that area
    # is equal to the window of interest area / size, then the window is covered.
    #
    # Note: The calculated area can't be larger than that!
    #
    #   1
    # D---C    => overlap given by H and B
    # | H-|---G  x-overlap: max(0, xleft2-xright1)
    # A---B   |     -> '1' and '2' is not known, that's why for left and right
    #   |  2  |      use min, each
    #   E-----F     -> max(0, min(xright1,xright2) - max(xleft1,xleft2) )
    #
    #            Note: Because of xleft<xright this can only
    #            result in xright1-xleft2 or xright2-xleft1
    #
    # All cases: 1 |    +--+|    +--+|+--+    |+--+    |
    #            2 |+--+    |  +--+  |  +--+  |    +--+|
    #      overlap |   0    |   2    |   2    |   0    |

    return max(0, min(x1+w1,x2+w2,x3+w3) - max(x1,x2,x3)) * \
        max(0, min(y1+h1,y2+h2,y3+h3) - max(y1,y2,y3))

def get_stacked_window_ids(window_id):
    # get all stacked window ids after and including the given wid
    window_ids = []

    for wid in ewmh.getClientListStacking():
        window_ids.append(wid)

    try:
        start = window_ids.index(window_id)
        end = len(window_ids)

        window_ids = window_ids[start:end]
    except (IndexError, ValueError):
        pass

    '''
    if len(window_ids) == 0:
        print("Couldn't find specified window id %s in _NET_CLIENT_LIST_STACKING(WINDOW)!" % window_id)
        
        sys.exit(2)

    if len(window_ids) == 1:
        fully_covered = False
    '''

    return window_ids

def get_window_coords(window_ids):
    ## Gather geometry of all windows in higher zorder / possibly lying on top
    coords = []

    for window_id in window_ids:
        # this is for caching purposes, to speed that part up a bit...
        window_id_geometry = window_id.get_geometry()
        window_id_parent_geometry = window_id.query_tree().parent.get_geometry()
        
        x = window_id_geometry.x + window_id_parent_geometry.x
        y = window_id_geometry.y + window_id_parent_geometry.y

        width = window_id_geometry.width
        height = window_id_geometry.height

        try:
            #property_ = ewmh.display.intern_atom('_NET_FRAME_EXTENTS')
            #type_ = Xatom.CARDINAL
            
            frame_left, frame_right, frame_top, frame_bottom = window_id.get_full_property(property_, type_).value
        except AttributeError:
            frame_left, frame_right, frame_top, frame_bottom = 0, 0, 0, 0

        coords.extend([x-frame_left, y-frame_top, width+frame_left+frame_right, height+frame_top+frame_bottom])

        #coords = [int(i) for i in coords]

    '''
    if len(coords) == 0:
        sys.exit(0)
    '''

    return coords

def is_fully_covered(window_id):
    window_ids = get_stacked_window_ids(window_id)
    coords = get_window_coords(window_ids)
    area = 0
    fully_covered = None

    # Calculate overlap with window in question
    # 0:x 1:y 2:w 3:h, border widths 0:frame_left 1:frame_right 2:frame_top 3:frame_bottom
    for i in range(4, len(coords), 4):
        area += overlap(* (coords[0:4] + coords[i:i+4]))

    # subtract double counted areas i.e. areas overlapping to the window
    # of interest and two other windows on top ... This is n**2
    for i in range(4, len(coords), 4):
        for j in range(i+4, len(coords), 4):
            area -= overlap(* (coords[0:4] + coords[i:i+4] + coords[j:j+4]))

    window_area = 0

    try:
        window_area = coords[2] * coords[3]

        fully_covered = (not (area < window_area))
    except IndexError:
        pass

    return fully_covered

'''
def _get_property(self, win, prop):
    """Gets an X Window's property, or None."""
    atom = win.get_full_property(self.dpy.intern_atom(prop), X.AnyPropertyType)
    if atom:
        return atom.value
    return None
'''

ewmh = ewmh.EWMH()
property_ = ewmh.dpy.intern_atom('_NET_FRAME_EXTENTS')
type_ = Xatom.CARDINAL

if __name__ == "__main__":
    for window_id in ewmh.getClientList():
        name = ewmh.getWmName(window_id)

        #property_ = ewmh.display.intern_atom('_NET_FRAME_EXTENTS')
        #type_ = Xatom.CARDINAL

        fully_covered = is_fully_covered(window_id)

        print("debug: [%s] [%-20.20s] [%s]" % (window_id, name, fully_covered))

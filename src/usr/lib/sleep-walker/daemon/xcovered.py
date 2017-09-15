#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import ewmh

from Xlib import X

class XCovered(object):
    def __init__(self, ewmh):
        self.ewmh = ewmh

    def get_window_coords(self, wid):
        # get all stacked window ids after and including the given wid
        wids = self.ewmh.getClientListStacking()
        wids = wids[wids.index(wid):]

        # gather geometry of all windows in higher zorder / possibly lying on top
        coords = []

        for wid in wids:
            if wid.get_attributes().map_state == X.IsViewable:
                parent_window_geometry = wid.query_tree().parent.get_geometry()
                window_geometry = wid.get_geometry()

                x_ = parent_window_geometry.x + window_geometry.x
                y_ = parent_window_geometry.y + window_geometry.y
                width = window_geometry.width
                height = window_geometry.height

                left, right, top, bottom = self.ewmh.getFrameExtents(wid)
                
                x = [x_, y_, width, height, left, right, top, bottom]

                # apply the frame width to the coordinates and window width
                # 0:x 1:y 2:w 3:h, border widths 4:left 5:right 6:top 7:bottom
                coords += [x[0]-x[4], x[1]-x[6], x[2]+x[4]+x[5], x[3]+x[6]+x[7]]

        return coords

    def overlap(self, x1,y1,w1,h1, x2,y2,w2,h2, x3=0,y3=0,w3=65535,h3=65535):
        # Calculates the area of the union of all overlapping areas. If that area
        # is equal to the window of interest area / size, then the window is covered.
        #
        # Note: The calculated area can't be larger than that!
        #
        #    1
        #  D---C      => overlap given by H and B
        #  | H-|---G    x-overlap: max(0, xleft2-xright1)
        #  A---B   |         -> '1' and '2' is not known, that's why for left and right
        #    |  2  |            use min, each
        #    E-----F         -> max(0, min(xright1,xright2) - max(xleft1,xleft2) )
        #
        #                       Note: Because of xleft<xright this can only
        #                       result in xright1-xleft2 or xright2-xleft1
        #
        # All cases: 1 |     +--+ |   +--+ | +--+   | +--+      |
        #            2 | +--+     | +--+   |   +--+ |      +--+ |
        #      overlap |    0     |    2   |    2   |     0     |
        return max(0, min(x1+w1,x2+w2,x3+w3) - max(x1,x2,x3)) * \
               max(0, min(y1+h1,y2+h2,y3+h3) - max(y1,y2,y3))

    def is_fully_covered(self, wid):
        # Find out if C is completely or only partially covered by A or B
        #
        #  +-----------+
        #  |   +---+   |
        #  |   | +-------+
        #  | C | |   B   |
        #  |   | +-------+
        #  +---| A |---+
        #      +---+
        #
        # @return 'True' if window is completely covered, 'False' if partially covered
        #
        # Note: Only tested with three windows like in sketch above, but
        #       it should also work for an arbitrary amount of overlapping windows
        if wid.get_attributes().map_state != X.IsViewable:
            return True

        coords = self.get_window_coords(wid)

        area = 0
        woi = coords[2]*coords[3]

        # Calculate overlap with window in question
        # 0:x 1:y 2:w 3:h, border widths 0:left 1:right 2:top 3:bottom
        for i in range(4, len(coords), 4):
            area += self.overlap(*(coords[0:4]+coords[i:i+4]))

        # subtract double counted areas i.e. areas overlapping to the window
        # of interest and two other windows on top ... This is n**2
        for i in range(4, len(coords), 4):
            for j in range(i+4, len(coords), 4):
                area -= self.overlap(*(coords[0:4]+coords[i:i+4]+coords[j:j+4]))
        
        return area >= woi

if __name__ == "__main__":
    ewmh = ewmh.EWMH()
    xc = XCovered(ewmh)

    for wid in ewmh.getClientList():
        if ewmh.getCurrentDesktop() == ewmh.getWmDesktop(wid):
            print("%s '%s' fully covered: %s" % (wid, ewmh.getWmName(wid), xc.is_fully_covered(wid)))


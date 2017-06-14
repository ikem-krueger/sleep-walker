#!/bin/bash
# Name: xcovered.sh
# Find out if C is completely or only partially covered by A or B
#  +-----------+
#  |   +===+   |
#  |   | +-------+
#  | C | |   B   |
#  |   | +-------+
#  +---| A |---+
#      +---+
# @return 0 if window ist not visible, 1 if visible
# Note: Only tested with three windows like in sketch above, but
#       it should also work for an arbitrary amount of overlapping windwows
wid=$1
if ! xwininfo -id $wid -stats | 'grep' -q 'IsViewable'; then return 0; fi

# get all stacked window ids after and including the given wid
wids=($(xprop -root | 'sed' -nE "/_NET_CLIENT_LIST_STACKING\(WINDOW\)/{ s|.*($wid)|\1|; s|,||g; p }"))
if [ ${#wids} -eq 0 ]; then
    echo -e "\e[31mCouldn't find specified window id $wid in _NET_CLIENT_LIST_STACKING(WINDOW)"'!'"\e[0m"
    return 2
fi
if [ ${#wids} -eq 1 ]; then return 0; fi

# Gather geometry of all windows in higher zorder / possibly lying on top
coords=(); frames=()
for owid in ${wids[@]}; do
    #xwininfo -id $owid | grep xwininfo
    if xwininfo -id $owid -stats | 'grep' -q 'IsViewable'; then
        # _NET_WM_ICON_GEOMETRY doesn't exist for xfce4-panel, thereby making this more difficult
        #coords=$(xprop -id $owid _NET_WM_ICON_GEOMETRY)
        #frames=$(xprop -id $owid _NET_FRAME_EXTENTS)
        x=($(xwininfo -id $owid -stats -wm | sed -nE '
            s|^[ \t]*Absolute upper-left X:[ \t]*([0-9]+).*|\1|Ip;
            s|^[ \t]*Absolute upper-left Y:[ \t]*([0-9]+).*|\1|Ip;
            s|^[ \t]*Width:[ \t]*([0-9]+).*|\1|Ip;
            s|^[ \t]*Height:[ \t]*([0-9]+).*|\1|Ip;
            /Frame extents:/I{ s|^[ \t}Frame Extents:[ \t]*||I; s|,||g; p; };
        ' | sed ':a; N; $!b a; s/\n/ /g '))
        if [ ! ${#x[@]} -eq 8 ]; then
            echo -e "\e[31mSomething went wrong when parsing the output of 'xwininfo -id $owid -stats -wm':\e[0m"
            xwininfo -id $owid -stats -wm
            exit 1
        fi
        # apply the frame width to the coordinates and window width
        # 0:x 1:y 2:w 3:h, border widths 4:left 5:right 6:top 7:bottom
        coords+=( "${x[0]}-${x[4]}, ${x[1]}-${x[6]}, ${x[2]}+${x[4]}+${x[5]}, ${x[3]}+${x[6]}+${x[7]}" )
    fi
done

IFS=','; python - <<EOF #| python
# Calculates the area of the union of all overlapping areas. If that area
# is equal to the window of interest area / size, then the window is covered.
# Note that the calcualted area can't be larger than that!
#   1
# D---C      => overlap given by H and B
# | H-|---G    x-overlap: max(0, xleft2-xright1)
# A---B   |         -> '1' and '2' is not known, that's why for left and right
#   |  2  |            use min, each
#   E-----F         -> max(0, min(xright1,xright2) - max(xleft1,xleft2) )
#                      Note that because of xleft<xright this can only
#                      result in xright1-xleft2 or xright2-xleft1
# All cases: 1 |     +--+ |   +--+ | +--+   | +--+      |
#            2 | +--+     | +--+   |   +--+ |      +--+ |
#      overlap |    0     |    2   |    2   |     0     |
def overlap( x1,y1,w1,h1, x2,y2,w2,h2, x3=0,y3=0,w3=65535,h3=65535 ):
    return max( 0, min(x1+w1,x2+w2,x3+w3) - max(x1,x2,x3) ) * \
           max( 0, min(y1+h1,y2+h2,y3+h3) - max(y1,y2,y3) )
x=[ ${coords[*]} ]
area=0
# Calculate overlap with window in question
# 0:x 1:y 2:w 3:h, border widths 0:left 1:right 2:top 3:bottom
for i in range( 4,len(x),4 ):
    area += overlap( *( x[0:4]+x[i:i+4] ) )

# subtract double counted areas i.e. areas overlapping to the window
# of interest and two other windows on top ... This is n**2
for i in range( 4,len(x),4 ):
    for j in range( i+4,len(x),4 ):
        area -= overlap( *( x[0:4]+x[i:i+4]+x[j:j+4] ) )

print "area =",area
print "woi  =",x[2]*x[3]
# exit code 0: if not fully covered, 1: if fully covered
exit( area < x[2]*x[3] )
EOF
exit $?

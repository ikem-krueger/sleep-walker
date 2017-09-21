#!/bin/bash
#
# firefox-suspender: Periodically check whether firefox is out of focus
# and STOP it in that case after a time delay; if in focus but stopped,
# send SIGCONT.
#
# (c) Petr Baudis <pasky@ucw.cz>  2014
# MIT licence if this is even copyrightable

loop_delay=1    # [s]
stop_delay=10   # [s]

last_in_focus=$(date +%s)
firefoxpid=
state=running

while true; do
	sleep $loop_delay

	# Get active window id
	window=$(xprop -root _NET_ACTIVE_WINDOW)
	window=${window#*# }
	# What kind of window is it?
	class=$(xprop -id "$window" WM_CLASS)
	# echo Active window $window, class $class

	if [[ "$class" =~ Navigator ]]; then
		# Firefox!  We know it is running.  Make sure we
		# have its pid and update the last seen date.
		# If we stopped it, resume again.
		if [ "$state" = stopped ]; then
			echo "$(date)  Resuming firefox @ $firefoxpid"
			if kill -CONT $firefoxpid; then
				state=running
			else
				firefoxpid=
			fi
		fi
		last_in_focus=$(date +%s)
		if [ -z "$firefoxpid" ]; then
			firefoxpid=$(pidof iceweasel)
		fi
		if [ -z "$firefoxpid" ]; then
			firefoxpid=$(pidof firefox)
		fi

		continue
	fi

	# Not Firefox!  If it's running, we are on battery and
	# it's been long enough, stop it now.
	if [ "$state" != running ]; then
		continue
	fi

	read battery </sys/class/power_supply/BAT0/status
	if [ "$battery" != Discharging ]; then
		continue
	fi

	if [ $(($(date +%s) - last_in_focus)) -ge $stop_delay ]; then
		echo "$(date)  Stopping firefox @ $firefoxpid"
		if ! kill -STOP $firefoxpid; then
			firefoxpid=
		fi
		state=stopped
	fi
done

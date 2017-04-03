#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import gtk

def show_popup_menu(data, event_button, event_time):
    popup_menu.popup(None, None, None, event_button, event_time)

builder = gtk.Builder()
builder.add_from_file("sleep-walker.glade")

popup_menu = builder.get_object("popup_menu")

status_icon = gtk.status_icon_new_from_file("sleep-walker.svg")
status_icon.connect("popup-menu", show_popup_menu)

gtk.main()

#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import gtk
import sys
from gui import *

glade_file = "/usr/lib/sleep-walker/tray-icon/tray-icon.glade"
icon_file = "/usr/lib/sleep-walker/tray-icon/tray-icon.svg"
license_file = "/usr/share/doc/sleep-walker/LICENSE"

builder = gtk.Builder()
builder.add_from_file(glade_file)

# add_dialog
add_dialog = builder.get_object("add_dialog")

# edit_whitelist
edit_whitelist = builder.get_object("edit_whitelist")
edit_whitelist.connect("delete-event", hide_window)

model = gtk.ListStore(gtk.gdk.Pixbuf, str, str)
treeview1 = builder.get_object("treeview1")
treeview1.set_model(model)
treeview1.set_headers_visible(False)

column = gtk.TreeViewColumn()
column.set_title("Application")
treeview1.append_column(column)

renderer = gtk.CellRendererPixbuf()
column.pack_start(renderer, expand=False)
column.add_attribute(renderer, 'pixbuf', 0)

renderer = gtk.CellRendererText()
column.pack_start(renderer, expand=True)
column.add_attribute(renderer, 'text', 1)

add_button = builder.get_object("add_button")
#add_button.connect("clicked", add_application, model)
add_button.connect("clicked", show_window, add_dialog)

remove_button = builder.get_object("remove_button")
remove_button.connect("clicked", remove_application_, treeview1, model)

# add_dialog
add_dialog.connect("delete-event", hide_window)
add_dialog.connect("close", hide_window)
add_dialog.connect("response", add_application, model, edit_whitelist)

# about_dialog
about_dialog = builder.get_object("about_dialog")
about_dialog.set_license(open(license_file).read())
about_dialog.connect("delete-event", hide_window)
about_dialog.connect("response", hide_window)

# popup_menu
popup_menu = builder.get_object("popup_menu")

popup_menu_item_show_hide = builder.get_object("popup_menu_item_show_hide")
popup_menu_item_start = builder.get_object("popup_menu_item_start")
popup_menu_item_stop = builder.get_object("popup_menu_item_stop")
popup_menu_item_info = builder.get_object("popup_menu_item_info")
popup_menu_item_quit = builder.get_object("popup_menu_item_quit")

# status_icon
status_icon = gtk.status_icon_new_from_file(icon_file)
status_icon.connect("activate", toggle_window, edit_whitelist, model)
status_icon.connect("popup-menu", show_popup_menu, popup_menu)

# popup_menu
popup_menu_item_show_hide.connect("activate", toggle_window, edit_whitelist, model)
popup_menu_item_start.connect("activate", start_daemon, popup_menu_item_start, status_icon)
popup_menu_item_stop.connect("activate", stop_daemon, popup_menu_item_stop, status_icon)
popup_menu_item_info.connect("activate", show_window, about_dialog)
popup_menu_item_quit.connect("activate", quit_program, popup_menu_item_quit, status_icon)

# edit_whitelist
imagemenuitem2 = builder.get_object("imagemenuitem2")
imagemenuitem2.connect("activate", start_daemon, popup_menu_item_start, status_icon)

imagemenuitem3 = builder.get_object("imagemenuitem3")
imagemenuitem3.connect("activate", stop_daemon, popup_menu_item_stop, status_icon)

imagemenuitem5 = builder.get_object("imagemenuitem5")
imagemenuitem5.connect("activate", quit_program, popup_menu_item_quit, status_icon)

imagemenuitem10 = builder.get_object("imagemenuitem10")
imagemenuitem10.connect("activate", show_window, about_dialog)

toolbutton1 = builder.get_object("toolbutton1")
toolbutton1.connect("clicked", start_daemon, popup_menu_item_start, status_icon)

toolbutton2 = builder.get_object("toolbutton2")
toolbutton2.connect("clicked", stop_daemon, popup_menu_item_stop, status_icon)

#statusbar1 = builder.get_object("statusbar1")
#statusbar1.push(0, "Daemon is running.")

#start_daemon(popup_menu_item_toggle)

gtk.main()

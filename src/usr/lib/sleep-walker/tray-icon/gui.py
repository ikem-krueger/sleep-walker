#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from ConfigParser import ConfigParser
import gtk
import subprocess
import os

def start_daemon(*args):
    global pid

    if notifications:
        show_notification("Starting daemon...")

    if not pid:
        pid = subprocess.Popen(["sleep-walker"]).pid # BUG: this is crap...

def stop_daemon(*args):
    global pid

    if notifications:
        show_notification("Stopping daemon...")

    if pid:
        subprocess.call(["kill", "-SIGTERM", "%s" % pid])

        pid = None

def toggle_daemon(*args):
    global pid
    
    popup_menu_item_toggle = args[0]
    status_icon = args[2]

    if not pid:
        start_daemon(popup_menu_item_toggle, status_icon)
    else:
        stop_daemon(popup_menu_item_toggle, status_icon)

def show_notification(message):
    # BUG: reusing the notification is not working properly on my laptop
    subprocess.Popen(["notify-send", "-h", "string:x-canonical-private-synchronous:sleep-walker", "-i", icon_file, "Sleep Walker", message])

def show_window(*args):
    window = args[1]
    
    window.show()

def toggle_window(*args):
    window = args[1]
    model = args[2]

    if window.get_property("visible"):
        window.hide()
    else:
        edit_whitelist_(None, window, model)

        window.show()

def hide_window(*args):
    for widget in args:
        if type(widget) in [gtk.Window, gtk.Dialog, gtk.AboutDialog, gtk.MessageDialog]:
            widget.hide()

            return True

def show_popup_menu(*args):
    time = args[2]
    popup_menu = args[3]

    popup_menu.popup(None, None, None, 0, time)

def fill_model(model):
    whitelist = set()

    for whitelist_file in [system_whitelist, user_whitelist]:
        if os.path.exists(whitelist_file):
            whitelist = whitelist.union(open(whitelist_file).read().split())

    for exe in whitelist:
        desktop_file = "/usr/share/applications/%s.desktop" % exe

        if os.path.exists("%s" % desktop_file):
            parser = ConfigParser()
            parser.read("%s" % desktop_file)

            name = parser.get("Desktop Entry", "Name")
            icon = parser.get("Desktop Entry", "Icon")
            icon_size = 22

            if icon.startswith("/"):
                icon_path = icon
            else:
                icon_theme = gtk.icon_theme_get_default()
                icon_path = icon_theme.lookup_icon(icon, icon_size, 0).get_filename()
                
            row = [gtk.gdk.pixbuf_new_from_file_at_size(icon_path, icon_size, icon_size), name, exe]
        
            model.append(row)

    return model

def edit_whitelist_(*args):
    window = args[1]
    model = args[2]
    
    model.clear()
    model = fill_model(model)

    window.show()

def add_application(*args):
    window = args[0]
    signal = args[1]
    model = args[2]
    edit_whitelist = args[3]

    CANCEL = -6
    CLOSE = -4

    if signal in [CANCEL, CLOSE]:
        window.hide()
        
        return

    pid = int(subprocess.check_output(["xprop", "_NET_WM_PID"]).split(" = ")[1])
    exe = subprocess.check_output(["readlink", "/proc/%s/exe" % pid]).strip().split("/")[-1]
    desktop_file = "/usr/share/applications/%s.desktop" % exe

    # to skip what we already have
    for row in model:
        if row[2] == exe:
            window.hide()
        
            return

    parser = ConfigParser()
    parser.read(desktop_file)

    name = parser.get("Desktop Entry", "Name")
    icon = parser.get("Desktop Entry", "Icon")
    icon_size = 22

    if icon.startswith("/"):
        icon_path = icon
    else:
        icon_theme = gtk.icon_theme_get_default()
        icon_path = icon_theme.lookup_icon(icon, icon_size, 0).get_filename()
        
    row = [gtk.gdk.pixbuf_new_from_file_at_size(icon_path, icon_size, icon_size), name, exe]
    
    model.insert(0, row)
    
    update_config_file(model)
    
    window.hide()

def remove_application_(*args):
    treeview1 = args[1]
    model = args[2]
    
    selection = treeview1.get_selection()
    model_, treeiter = selection.get_selected()

    exe = model[treeiter][2]

    model.remove(treeiter)

    update_config_file(model)

def update_config_file(*args):
    model = args[0]
    
    current_whitelist = []
    
    for row in model:
        exe = row[2]
        
        current_whitelist.append(exe)
        
    if uid == 0:
        whitelist_file = system_whitelist
    else:
        whitelist_file = user_whitelist

    whitelist_path = whitelist_file.rstrip("/whitelist")

    try:
        os.makedirs(whitelist_path)
    except OSError, e:
        # if path exists...
        if e.errno == 17:
            pass
    
    with open(whitelist_file, "w") as f:
        f.write("\n".join(current_whitelist))

def quit_program(*args):
    popup_menu_item_toggle = args[1]
    status_icon = args[2]
    
    stop_daemon(popup_menu_item_toggle, status_icon)

    gtk.main_quit()

uid = os.getuid()
home = os.getenv("HOME")

system_whitelist = "/etc/sleep-walker/whitelist"
user_whitelist = "%s/.sleep-walker/whitelist" % home

icon_file = "/usr/lib/sleep-walker/tray-icon/tray-icon.svg"

notifications = True
pid = None

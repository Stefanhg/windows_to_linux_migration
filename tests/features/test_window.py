"""A real, uniquely titled GTK application owned exclusively by the test."""
import sys
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

window = Gtk.Window(title=sys.argv[1])
window.set_default_size(640, 400)
window.add(Gtk.Label(label='Desktop acceptance test — this window closes automatically.'))
window.connect('destroy', Gtk.main_quit)
window.show_all()
Gtk.main()

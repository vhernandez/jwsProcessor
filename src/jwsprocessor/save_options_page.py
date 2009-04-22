#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import pygtk
pygtk.require("2.0")
import gtk
from tools import _

class SaveOptionsPage(gtk.VBox):
    SO_ONEFILE_ONEX = 1
    SO_ONEFILE_MULTIPLEX = 2
    SO_MULTIPLE_FILES = 3
    SO_DONT_SAVE = 0

    def __init__(self, assistant):
        self.assistant = assistant
        self._create_widgets()

    def _create_widgets(self):
        gtk.VBox.__init__(self)
        option1 = gtk.RadioButton(label=_("Save only one file, with a single X column"))
        option2 = gtk.RadioButton(label=_("Save only one file, with multiple X columns"),
                                  group=option1)
        option3 = gtk.RadioButton(label=_("Save in multiple files"),
                                  group=option1)
        option4 = gtk.RadioButton(label=_("Don't save"),
                                  group=option1)

        column_headers = gtk.CheckButton(_("Write the name of each column"))
        column_headers.set_active(False)
        self.get_column_headers_option = column_headers.get_active

        self.pack_start(option1, False, False, 0)
        self.pack_start(option2, False, False, 0)
        self.pack_start(option3, False, False, 0)
        self.pack_start(option4, False, False, 0)
        self.pack_start(gtk.HSeparator(), False, False, 0)
        self.pack_start(column_headers, False, False, 0)
        self.show_all()
        
        self.onefile_onex = option1
        self.onefile_multiplex = option2
        self.multiplefiles = option3
        self.dontsave = option4
#        self.column_headers = column_headers
        
    def get_option(self):
        if self.onefile_onex.get_active():
            return self.SO_ONEFILE_ONEX
        elif self.onefile_multiplex.get_active():
            return self.SO_ONEFILE_MULTIPLEX
        elif self.multiplefiles.get_active():
            return self.SO_MULTIPLE_FILES
        else:
            return self.SO_DONT_SAVE

    

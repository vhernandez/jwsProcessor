#!/usr/bin/env python
# -*- coding: UTF8 -*-
import pygtk
pygtk.require("2.0")
import gtk

class SummaryPage(gtk.VBox):
    def __init__(self, assistant):        
        self.assistant = assistant

        gtk.VBox.__init__(self)
        self._create_widgets()

    def set_message(self, message, info_buffer, image_type=gtk.STOCK_DIALOG_INFO):
        self.message_label.set_text(message)
        self.message_image.set_from_stock(image_type, gtk.ICON_SIZE_DIALOG)
        self.details_text.set_buffer(info_buffer)

    def _create_widgets(self):
        self.message_label = gtk.Label()
        self.message_image = gtk.Image()
        message_hbox = gtk.HBox()
        message_hbox.pack_start(self.message_image, False, False, 5)
        message_hbox.pack_start(self.message_label, False, False, 5)
        self.details_text = gtk.TextView()
        self.details_text.props.editable = False
        details_scroll = gtk.ScrolledWindow()
        details_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        details_scroll.add(self.details_text)        
        self.pack_start(message_hbox, False, False, 5)
        self.pack_end(details_scroll, True, True, 5)        
        #self.set_size_request(580,-1)

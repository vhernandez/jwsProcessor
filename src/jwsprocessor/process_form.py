#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import pygtk
pygtk.require("2.0")
import gtk
from tools import wait_till_refresh, _


class ProcessForm(gtk.Window):
    def __init__(self, parent=None):
        self.parent_form = parent
        self.loop_running = False
        self.base_label_text = _("Processing files...")

        gtk.Window.__init__(self)
        self.create_widgets()
        
    def start_loop(self):
        self.show()
        self.loop_running = True
        self.close_button.set_sensitive(False)
        wait_till_refresh()

    def abort_loop(self):
        self.close_button.set_sensitive(True)
        self.loop_running = False
        # Más cosas!!!

    def finish_loop(self):
        self.close_button.set_sensitive(True)
        self.loop_running = False

    def delete_event_cb(self, widget, event, user_data=None):
        ''' Returns True if main_loop function is running, this stops the
            deletion.            
        '''
        return self.loop_running
        
    def close_cb(self, widget, user_data=None):
        if not self.loop_running:        
            self.destroy()

    def reset(self):
        if not self.loop_running:
            self.set_title()
            self.update_progress(progress=0.0,
                                 title=self.base_label_text)

    def update_progress(self, progress, title):              
        self.progressbar.set_fraction(progress)
        self.progressbar.props.text = "%.0f%%" % (progress*100.0)
        self.set_title(title)
        wait_till_refresh()
        
    def create_widgets(self):        
        self.progressbar = gtk.ProgressBar()
        self.details_text = gtk.TextView()
        self.details_text.props.editable = False
        self.details_buffer = self.details_text.get_buffer()
        self.details_buffer.create_tag("redtag", foreground="red")        
        self.close_button = gtk.Button(stock=gtk.STOCK_CLOSE)

        closebtn_hbox = gtk.HBox()
        closebtn_hbox.pack_end(self.close_button, False, False, 0)
        mainvbox = gtk.VBox()
        mainvbox.set_homogeneous(False)      
        mainvbox.pack_start(self.progressbar, False, False, 5)              
        mainvbox.pack_end(closebtn_hbox, False, False, 5)
        mainvbox.pack_end(gtk.HSeparator(), False, False, 5) 

        self.update_progress(progress=0.0, title=self.base_label_text)
        self.set_border_width(5)
        self.set_size_request(400,-1)
        if self.parent_form!=None:
            self.set_transient_for(self.parent_form)
        self.set_modal(True)
        self.set_type_hint (gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.add(mainvbox)

        self.show_all()

        self.hide()

        self.close_button.connect("clicked", self.close_cb)
        self.connect("delete_event", self.delete_event_cb)


if __name__=="__main__":
    pf = ProcessForm()
    pf.show()
    gtk.main()
    

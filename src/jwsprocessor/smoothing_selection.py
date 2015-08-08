#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from matplotlib.axes import Subplot
from matplotlib.figure import Figure
# backend para matplotlib, por defecto gtkagg
from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
import pygtk
pygtk.require("2.0")
import gtk
import os
from numpy import array, arange, float32
import pysmoothing
import jwslib
from tools import ProcessOptions, _


class SmoothingSelectionDialog(gtk.Dialog):
    def __init__(self, header, channels, options, parent=None, 
                 title=_("Choose smoothing type"), 
                 buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK)):
        gtk.Dialog.__init__(self,
                            title=title, 
                            parent=parent, 
                            flags=gtk.DIALOG_MODAL,
                            buttons=buttons)
        self.header = header
        self.channels = channels
        self.options = options        
        self.xdata = arange(header.x_for_first_point,                    #start
                            header.x_for_last_point+header.x_increment,  #end+incr.
                            header.x_increment)                          #increment
        self.ellipticity = array(self.channels[0], float32)
        
        self._create_widgets()
        self._configure_widgets()
        self._plot_spectrum()

    def _smoothing_changed_cb(self, widget, user_data=None):
        self._refresh_options()
        if self.options.smoothing and (self.options.smoothing_type == "sg"):
            self.sp_hbox.show()
        else:
            self.sp_hbox.hide()
        self._plot_spectrum()

    def _plot_spectrum(self):
        self.figure.clear()        
        # Construct xdata (an array with x value for each point)        
        m = self.options.m
        p = self.figure.add_subplot(111)
        if self.options.smoothing:
            if (m % 2) == 0: m += 1
            if self.options.smoothing_type == "mm":
                smoothed = pysmoothing.mean_movement(self.ellipticity, m)                
            elif self.options.smoothing_type == "sg":                                          
                smoothed = pysmoothing.sgolayfilt(self.ellipticity, self.options.p, m)                
            p.plot( self.xdata, self.ellipticity, "b",  # a- Original data
                    self.xdata, smoothed, "r")  # b- Processed data
            #p.legend(("Original","Processed"))
        else:
            p.plot( self.xdata, self.ellipticity)
        self.canvas.draw()

    def _refresh_options(self,widget=None):        
        st = self.smoothing_combo.get_active()       
        if st==2:
            self.options.smoothing = False
        else:
            self.options.smoothing = True
        if st==1:
            self.options.smoothing_type = "sg"            
        elif st==0:
            self.options.smoothing_type = "mm"
        self.options.m = int(self.m_spinner.get_value())
        self.options.set_clamped_p(int(self.p_spinner.get_value()))
            
    def _configure_widgets(self):
        self.m_spinner.set_value(self.options.m)
        if self.options.smoothing_type == "mm":
            self.smoothing_combo.set_active(0)
        elif self.options.smoothing_type == "sg":
            self.smoothing_combo.set_active(1)
        else:
            self.smoothing_combo.set_active(2)
        self.p_spinner.set_value(self.options.get_clamped_p())
        self.smoothing_combo.connect("changed", self._smoothing_changed_cb)
        self.m_spinner.connect("value-changed", self._smoothing_changed_cb)
        self.p_spinner.connect("value-changed", self._smoothing_changed_cb)
        if self.options.smoothing and (self.options.smoothing_type == "sg"):
            self.sp_hbox.show()
        else:
            self.sp_hbox.hide()
        
    def _create_widgets(self):
        def create_label(text):
            label = gtk.Label(text)
            label.show()
            return label

        self.smoothing_list = gtk.ListStore(str)
        smoothing_types = ("Mean-movement", "Savitsky-Golay", _("No smoothing"))
        for smt in smoothing_types:
            self.smoothing_list.append([smt])        
        cell = gtk.CellRendererText()        
        self.smoothing_combo = gtk.ComboBox(self.smoothing_list)
        self.smoothing_combo.pack_start(cell, True)
        self.smoothing_combo.add_attribute(cell, 'text', 0)
        self.smoothing_combo.show()
        self.m_spinner = gtk.SpinButton()
        self.m_spinner.set_range(5, 25)
        self.m_spinner.set_increments(1,5)                
        self.m_spinner.show()
        self.p_spinner = gtk.SpinButton()
        self.p_spinner.set_range(1,6)
        self.p_spinner.set_increments(1,1)
        self.p_spinner.show()

        sc_hbox = gtk.HBox()
        sc_hbox.pack_start(create_label(_("Smoothing type:")), False, False, 0)
        sc_hbox.pack_end(self.smoothing_combo, False, True, 0)
        sc_hbox.show()
        sm_hbox = gtk.HBox()
        sm_hbox.pack_start(create_label(_("Smoothing level(m):")), False, False, 0)
        sm_hbox.pack_end(self.m_spinner, False, False, 0)
        sm_hbox.show()
        sp_hbox = gtk.HBox()
        sp_hbox.pack_start(create_label(_("S-G filter order (p):")), False, False, 0)
        sp_hbox.pack_end(self.p_spinner, False, False, 0)
        sp_hbox.show()
        self.sp_hbox = sp_hbox

        self.figure = Figure(figsize=(5,4))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.show()
        self.vbox.pack_start(sc_hbox, False, False, 0)
        self.vbox.pack_start(sm_hbox, False, False, 0)
        self.vbox.pack_start(sp_hbox, False, False, 0)
        self.vbox.pack_start(self.canvas, True, True, 0)        
        self.set_default_size(400,400)

class ShowSpectrumDialog(SmoothingSelectionDialog):
    def __init__(self, input_fn, options=ProcessOptions(), parent=None):
        results = jwslib.read_file(input_fn)
        error = True
        if results[0] == jwslib.JWS_ERROR_SUCCESS:
            header = results[1]                
            channels = results[2]
            if len(channels) > 0:
                error = False
        if error:
            raise Exception, "File %s could not be loaded" % input_fn
        (head, tail) = os.path.split(input_fn) # head=path; tail=nombre arch.
        title = _("Showing %s") % tail
        SmoothingSelectionDialog.__init__(self, header, channels, options, 
                                          parent, title, 
                                          (gtk.STOCK_CLOSE, gtk.RESPONSE_OK))



class ShowSpectrumPanel(gtk.VBox):
    def __init__(self, options=ProcessOptions(), parent=None):
        gtk.VBox.__init__(self)
        self.header = None
        self.channels = None
        self.ellipticity = None
        self.xdata = None
        self.options=options 
        self._create_widgets()

    def show_spectrum_file(self, input_fn, options=None):
        results = jwslib.read_file(input_fn)
        error = True
        if results[0] == jwslib.JWS_ERROR_SUCCESS:
            header = results[1]                
            channels = results[2]
            if len(channels) > 0:
                error = False
        if error:
            return False
        else:
            if options is not None:
                self.options = options
            self.show_spectrum(header, channels)
            return True


    def show_spectrum(self, header, channels, options=None):
        self.header = header
        self.channels = channels
        if options is not None:
            self.options = options
        self.xdata = arange(header.x_for_first_point,                    #start
                            header.x_for_last_point+header.x_increment,  #end+incr.
                            header.x_increment)                          #increment
        self.ellipticity = array(self.channels[0], float32)
        
        self._configure_widgets()
        self._plot_spectrum()

    def _smoothing_changed_cb(self, widget, user_data=None):
        self._refresh_options()
        if self.options.smoothing and (self.options.smoothing_type == "sg"):
            self.sp_hbox.show()
        else:
            self.sp_hbox.hide()
        self._plot_spectrum()

    def _plot_spectrum(self):
        self.figure.clear()        
        # Construct xdata (an array with x value for each point)        
        m = self.options.m
        p = self.figure.add_subplot(111)
        if self.options.smoothing:
            if (m % 2) == 0: m += 1
            if self.options.smoothing_type == "mm":
                smoothed = pysmoothing.mean_movement(self.ellipticity, m)                
            elif self.options.smoothing_type == "sg":                                          
                smoothed = pysmoothing.sgolayfilt(self.ellipticity, self.options.p, m)                
            p.plot( self.xdata, self.ellipticity, "b",  # a- Original data
                    self.xdata, smoothed, "r")  # b- Processed data
            #p.legend(("Original","Processed"))
        else:
            p.plot( self.xdata, self.ellipticity)
        self.canvas.draw()

    def _refresh_options(self,widget=None):        
        st = self.smoothing_combo.get_active()       
        if st==2:
            self.options.smoothing = False
        else:
            self.options.smoothing = True
        if st==1:
            self.options.smoothing_type = "sg"            
        elif st==0:
            self.options.smoothing_type = "mm"
        self.options.m = int(self.m_spinner.get_value())
        self.options.set_clamped_p(int(self.p_spinner.get_value()))
            
    def _configure_widgets(self):
        self.m_spinner.set_value(self.options.m)
        if self.options.smoothing_type == "mm":
            self.smoothing_combo.set_active(0)
        elif self.options.smoothing_type == "sg":
            self.smoothing_combo.set_active(1)
        else:
            self.smoothing_combo.set_active(2)
        self.p_spinner.set_value(self.options.get_clamped_p())
        self.smoothing_combo.connect("changed", self._smoothing_changed_cb)
        self.m_spinner.connect("value-changed", self._smoothing_changed_cb)
        self.p_spinner.connect("value-changed", self._smoothing_changed_cb)
        if self.options.smoothing and (self.options.smoothing_type == "sg"):
            self.sp_hbox.show()
        else:
            self.sp_hbox.hide()
        
    def _create_widgets(self):
        def create_label(text):
            label = gtk.Label(text)
            label.show()
            return label

        self.smoothing_list = gtk.ListStore(str)
        smoothing_types = ("Mean-movement", "Savitsky-Golay", _("No smoothing"))
        for smt in smoothing_types:
            self.smoothing_list.append([smt])        
        cell = gtk.CellRendererText()        
        self.smoothing_combo = gtk.ComboBox(self.smoothing_list)
        self.smoothing_combo.pack_start(cell, True)
        self.smoothing_combo.add_attribute(cell, 'text', 0)
        self.smoothing_combo.show()
        self.m_spinner = gtk.SpinButton()
        self.m_spinner.set_range(5, 25)
        self.m_spinner.set_increments(1,5)                
        self.m_spinner.show()
        self.p_spinner = gtk.SpinButton()
        self.p_spinner.set_range(1,6)
        self.p_spinner.set_increments(1,1)
        self.p_spinner.show()

        sc_hbox = gtk.HBox()
        sc_hbox.pack_start(create_label(_("Smoothing type:")), False, False, 0)
        sc_hbox.pack_end(self.smoothing_combo, False, True, 0)
        sc_hbox.show()
        sm_hbox = gtk.HBox()
        sm_hbox.pack_start(create_label(_("Smoothing level (m):")), False, False, 0)
        sm_hbox.pack_end(self.m_spinner, False, False, 0)
        sm_hbox.show()
        sp_hbox = gtk.HBox()
        sp_hbox.pack_start(create_label(_("S-G filter order (p):")), False, False, 0)
        sp_hbox.pack_end(self.p_spinner, False, False, 0)
        sp_hbox.show()
        self.sp_hbox = sp_hbox

        self.figure = Figure(figsize=(5,4))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.show()
        self.pack_start(sc_hbox, False, False, 0)
        self.pack_start(sm_hbox, False, False, 0)
        self.pack_start(sp_hbox, False, False, 0)
        self.pack_start(self.canvas, True, True, 0)        
        #self.set_default_size(400,400)



if __name__=="__main__":
    # Read input file
    ssd = ShowSpectrumDialog('../data/Punto#001.jws')
    ssd.run()




        
        

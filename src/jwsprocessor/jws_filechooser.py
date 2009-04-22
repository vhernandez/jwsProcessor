#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import pygtk
pygtk.require("2.0")
import gtk
import jwslib
from matplotlib.axes import Subplot
from matplotlib.figure import Figure
# backend para matplotlib, por defecto gtkagg
from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
from numpy.oldnumeric import array, arange, Float
from tools import _

# Estructuras ------------------------------------------------------------------
ff_jws = gtk.FileFilter()
ff_jws.set_name(_("JWS files"))
ff_jws.add_pattern("*.jws")

ff_txt = gtk.FileFilter()
ff_txt.set_name(_("TXT files"))
ff_txt.add_pattern("*.txt")

class JwsFileChooserDialog(gtk.FileChooserDialog):
    def __init__(self, parent, current_folder=None, title=_("Open spectra...")):
        gtk.FileChooserDialog.__init__(self, 
                title=title, 
                parent= parent,
                action= gtk.FILE_CHOOSER_ACTION_OPEN,
                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                        gtk.STOCK_ADD, gtk.RESPONSE_OK))
        self.figure = Figure(figsize=(5,4))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.set_size_request(200,200) #tamaño mínimo del widget        
        self.add_filter(ff_jws)
        self.set_select_multiple(True)
        if current_folder:
            self.set_current_folder(current_folder)
        self.set_preview_widget(self.canvas)
        self.connect("selection-changed", self._update_preview_cb)
        self.show_all()

    def _update_preview_cb(self, widget):
        input_fn = self.get_preview_filename()
        results = jwslib.read_file(input_fn)
        error = True
        if results[0] == jwslib.JWS_ERROR_SUCCESS:
            header = results[1]                
            channels = results[2]
            if len(channels) > 0:
                error = False
        if not error:                            
            xdata = arange(header.x_for_first_point,                  #start
                           header.x_for_last_point+header.x_increment,#end+incr.
                           header.x_increment)                        #increment
            ellipticity = array(channels[0], Float)
            self.figure.clear()
            p = self.figure.add_subplot(111)
            p.plot( xdata, ellipticity)
            self.canvas.draw()
        self.set_preview_widget_active(not error)

if __name__=="__main__":        
    fs_dialog = JwsFileChooserDialog( parent=None )
    response = fs_dialog.run()
    if response == gtk.RESPONSE_OK:
        #En windows hay que recodificar los nombres de archivo!!
        fns = [fn.decode('utf-8') for fn in fs_dialog.get_filenames()]
    else:
        fns = None
    if fns:
        print fns
    fs_dialog.destroy()

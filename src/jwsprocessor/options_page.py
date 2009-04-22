#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
* Crear un diálogo para calcular el factor de corrección
* Crear una base de datos de proteínas, guardando su Peso Molecular y
  Número de Residuos
"""
import pygtk
pygtk.require("2.0")
import gtk
import gobject
import os
import jwslib
from jws_filechooser import JwsFileChooserDialog
from fc_calculator import CDCorrectionFactorCalculator
from tools import _


class OptionsPage(gtk.VBox):
    def __init__(self, options, assistant, current_folder=os.getcwd()):
        gtk.VBox.__init__(self)
        self.options = options
        self.assistant = assistant
        self.current_folder = current_folder
        self._create_widgets()
        self._configure_widgets()

    def _create_widgets(self):
        def create_label(text):
            label = gtk.Label(text)
            label.show()
            return label

        #Blanco
        self.subtract_blank_btn = gtk.CheckButton(_("Substract blank"))
        self.blank_entry = gtk.Entry()
        self.blank_entry.props.editable = False
        self.blank_open_button = gtk.Button(stock=gtk.STOCK_OPEN)
        #Multiplicar factores de dilución
        self.dilution_btn = gtk.CheckButton(_("Multiply dilution factors"))
        #Elipticidad a 260nm
        self.subtract260_btn = gtk.CheckButton(_("Substract ellipticity at 260nm"))
        #Smoothing
        self.apply_smoothing_btn = gtk.CheckButton(_("Apply smoothing"))
        self.smoothing_list = gtk.ListStore(str)
        self.smoothing_list.append(["Mean-movement"])
        self.smoothing_list.append(["Savitsky-Golay"])
        cell = gtk.CellRendererText()
        self.smoothing_combo = gtk.ComboBox(self.smoothing_list)
        self.smoothing_combo.pack_start(cell, True)
        self.smoothing_combo.add_attribute(cell, 'text', 0)        
        self.m_scale = gtk.HScale()
        self.m_scale.set_range(2, 12)
        self.m_scale.set_increments(1, 1)
        self.m_scale.set_digits(0)
        self.p_scale = gtk.HScale()
        self.p_scale.set_range(2,6)
        self.p_scale.set_increments(1,1)
        self.p_scale.set_digits(0)
        #Factor de corrección
        self.apply_CF = gtk.CheckButton(_("Apply correction factor"))
        self.CF_spinner = gtk.SpinButton() 
        self.CF_spinner.set_range(-1000000000000.0,1000000000000.0)
        self.CF_spinner.set_digits(4)
        self.CF_spinner.set_increments(1, 10)
        self.calc_CF_btn = gtk.Button("Calcular...")

        cf_hbox = gtk.HBox()
        cf_hbox.pack_start(create_label(_("Correction factor:")), False, False, 0)
        cf_hbox.pack_end(self.CF_spinner)
        cfb_hbox = gtk.HBox()
        cfb_hbox.pack_end(self.calc_CF_btn)
        cf_vbox = gtk.VBox()
        cf_vbox.pack_start(self.apply_CF, False, False, 0)
        cf_vbox.pack_start(cf_hbox, False, False, 0)
        cf_vbox.pack_start(cfb_hbox, False, False, 0)
        cf_frame = gtk.Frame(_("Correction factor:"))
        cf_frame.add(cf_vbox)
        
        sc_hbox = gtk.HBox()
        sc_hbox.pack_start(create_label(_("Smoothing type:")), False, False, 0)
        sc_hbox.pack_end(self.smoothing_combo, False, True, 0)
        sm_hbox = gtk.HBox()
        sm_hbox.pack_start(create_label(_("Smoothing level(m):")), False, False, 0)
        sm_hbox.pack_end(self.m_scale, True, True, 0)
        sp_hbox = gtk.HBox()
        sp_hbox.pack_start(create_label(_("S-G filter order (p):")), False, False, 0)
        sp_hbox.pack_end(self.p_scale, True, True, 0)
        self.sp_hbox = sp_hbox
        so_vbox = gtk.VBox()
        so_vbox.pack_start(sc_hbox, False, False, 0)
        so_vbox.pack_start(sm_hbox, False, False, 0)
        so_vbox.pack_start(sp_hbox, False, False, 0)
        so_vbox.set_border_width(5)
        smoothing_frame = gtk.Frame(_("Smoothing options"))
        smoothing_frame.add(so_vbox)
        blank_hbox = gtk.HBox()
        blank_hbox.pack_start(self.blank_entry, True, True, 0)
        blank_hbox.pack_end(self.blank_open_button, False, False, 0)
        blank_vbox = gtk.VBox()
        blank_vbox.pack_start(self.subtract_blank_btn, False, False, 0)
        blank_vbox.pack_start(blank_hbox, False, False, 0)
        blank_frame = gtk.Frame(_("Blank:"))
        blank_frame.add(blank_vbox)
        
        self.pack_start(blank_frame, False, False, 0)
        self.pack_start(self.dilution_btn, False, False, 0)
        self.pack_start(self.subtract260_btn, False, False, 0)
        self.pack_start(self.apply_smoothing_btn, False, False, 0)
        self.pack_start(smoothing_frame, False, False, 0)
        self.pack_start(cf_frame, False, False, 0)
                
    def refresh_options(self,widget=None):
        self.options.blank_fn = self.blank_entry.get_text().decode('utf-8')
        self.options.subtract_blank = self.subtract_blank_btn.get_active()
        self.options.subtract260 = self.subtract260_btn.get_active()
        self.options.correct_dilution = self.dilution_btn.get_active()
        st = self.smoothing_combo.get_active()
        if st==1:
            self.options.smoothing_type = "sg"
        else:
            self.options.smoothing_type = "mm"            
        self.options.set_clamped_m(int((self.m_scale.get_value()*2)+1))
        self.options.set_clamped_p(int(self.p_scale.get_value()))
        self.options.correct = self.apply_CF.get_active()
        self.options.correction_factor = float(self.CF_spinner.get_value())
        
    def get_options(self):
        self.refresh_options()
        return self.options

    def set_smoothing_options(self, options):
        self.options.smoothing = options.smoothing
        self.options.smoothing_type = options.smoothing_type
        self.options.m = options.m
        self.options.p = options.p
        self._configure_widgets()

    def _configure_widgets(self):
        self.subtract_blank_btn.set_active(self.options.subtract_blank)
        self.blank_entry.set_sensitive(self.options.subtract_blank)
        self.blank_open_button.set_sensitive(self.options.subtract_blank)
        if self.options.blank_fn:
            self.blank_entry.set_text(self.options.blank_fn)
        #self.check_blank_options()
        self.subtract260_btn.set_active(self.options.subtract260)
        self.dilution_btn.set_active(self.options.correct_dilution)
        self.apply_smoothing_btn.set_active(self.options.smoothing)        
        self.m_scale.set_value(int((self.options.get_clamped_m()-1)/2))        
        if self.options.smoothing_type == "sg":
            self.smoothing_combo.set_active(1)
        else:
            self.smoothing_combo.set_active(0)
        self.p_scale.set_value(self.options.get_clamped_p())        
        if self.options.smoothing and (self.options.smoothing_type == "sg"):
            self.sp_hbox.show()
        else:
            self.sp_hbox.hide()
        self.apply_CF.set_active(self.options.correct)
        self.CF_spinner.set_value(self.options.correction_factor)
        self.CF_spinner.set_sensitive(self.options.correct)
        self.calc_CF_btn.set_sensitive(self.options.correct)

        self.subtract_blank_btn.connect("toggled", self._subtract_blank_toggled_cb)
        self.blank_entry.connect("changed", self.check_blank_options)
        self.sp_hbox.connect("show", self._sp_hbox_show_cb)
        self.blank_open_button.connect("clicked", self.blank_open_cb)
        self.apply_smoothing_btn.connect("toggled", self._smoothing_toggled_cb)
        self.smoothing_combo.connect("changed", self._smoothing_changed_cb)
        self.m_scale.connect("format-value", self._m_scale_changed_cb)
        self.apply_CF.connect("toggled", self._apply_CF_toggled_cb)
        self.calc_CF_btn.connect("clicked", self._calc_CF_btn_cb)

    def _calc_CF_btn_cb(self, widget):
        cfc = CDCorrectionFactorCalculator(parent=self.assistant)
        response = cfc.run()
        if response == gtk.RESPONSE_ACCEPT:
            print cfc.correction_factor #debug
            self.CF_spinner.set_value(cfc.correction_factor)
            self.options.correction_factor = self.CF_spinner.get_value()
        cfc.destroy()

    def _sp_hbox_show_cb(self, widget):
        if self.options.smoothing_type == "mm":
            self.sp_hbox.hide()

    def _smoothing_toggled_cb(self, widget, data=None):
        self.options.smoothing = self.apply_smoothing_btn.get_active()
        self.smoothing_combo.set_sensitive(self.options.smoothing)
        self.m_scale.set_sensitive(self.options.smoothing)
    
    def blank_open_cb(self, button, user_data=None):
        fs_dialog = JwsFileChooserDialog( parent= self.assistant,
                                          current_folder = self.current_folder,
                                          title=_("Open spectrum..."))        
        fs_dialog.set_select_multiple(False)
        response = fs_dialog.run()
        if response == gtk.RESPONSE_OK:
            fn = fs_dialog.get_filename().decode('utf-8')
            header = jwslib.read_header(fn)
            if header:
                self.blank_entry.set_text(fn)
                self.blank_header = header
                self.current_folder = fs_dialog.get_current_folder().decode('utf-8')
        fs_dialog.destroy()

    def _m_scale_changed_cb(self, widget, value, data=None):
        return ("%d" % int((value*2)+1))

    def _apply_CF_toggled_cb(self, widget, data=None):
        active = widget.get_active()
        self.CF_spinner.set_sensitive(active)
        self.calc_CF_btn.set_sensitive(active)
        
    def _subtract_blank_toggled_cb(self, widget, data=None):
        subtract_blank = self.subtract_blank_btn.get_active()
        self.blank_open_button.set_sensitive(subtract_blank)
        self.blank_entry.set_sensitive(subtract_blank)
        self.check_blank_options()

    def check_blank_options(self, widget=None, data=None):
        subtract_blank = self.subtract_blank_btn.get_active()
        allow_go = not (subtract_blank and (self.blank_entry.get_text()==""))
        self.assistant.set_page_complete(self, allow_go)

    def _smoothing_changed_cb(self, widget, data=None):
        st = self.smoothing_combo.get_active()
        if st==1:
            self.options.smoothing_type = "sg"
            self.sp_hbox.show()
        else:
            self.options.smoothing_type = "mm"
            self.sp_hbox.hide()


if __name__=="__main__":
    from tools import ProcessOptions                
    options = OptionsDialog(options=ProcessOptions())
    options.run()

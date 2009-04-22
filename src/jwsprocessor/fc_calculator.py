#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
To convert from mdeg to molar elipticity (deg*cm2*dmol-1):

m.e. =  mdeg / (10*l*(C/MW)*Rn)

where
l = light path in cm
C = concentration in mg/ml
MW = molecular weight
Rn = number of residue of the protein
"""
import pygtk
pygtk.require("2.0")
import gtk
import gobject
from tools import _

CU_WEIGHT_VOL = 0
CU_MICROMOLAR = 1
CU_MILIMOLAR = 2
CONC_UNITS_LIST = [CU_WEIGHT_VOL, CU_MICROMOLAR, CU_MILIMOLAR]


class ProteinInfo:
    def __init__(self, name, molecular_weight, residue_number, 
                 def_lp = 0.1, def_c=0.1, def_c_units = CU_WEIGHT_VOL):
        self.name = name
        self.molecular_weight = molecular_weight
        self.residue_number = residue_number
        self.default_light_path = def_lp
        self.default_concentration = def_c
        if def_c_units in CONC_UNITS_LIST:
            self.default_conc_units = def_c_units
        else:
            self.default_conc_units = CU_WEIGHT_VOL

    def get_c_units(self):
        if not self.default_conc_units in CONC_UNITS_LIST:
            self.default_conc_units = CU_WEIGHT_VOL
        return self.default_conc_units

        
class CDCorrectionFactorCalculator(gtk.Dialog):
    c_text = _("Concentration (%s):")

    def __init__(self, initial_params=ProteinInfo("C-LytA", 15840, 136), 
                 parent=None):
        gtk.Dialog.__init__(self, title=_("Calculate correction factor"),
                            parent=parent, flags=gtk.DIALOG_MODAL,
                            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                     gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self._create_widgets()
        self._configure_widgets(initial_params)
        self.protein_info = initial_params
        self.correction_factor = 0

    def _calculate_fc(self):
        cu = self.c_units_combo.get_active()        
        if cu ==CU_MICROMOLAR: # uM
            C = self.C_spinner.get_value() / 1000000.0
        elif cu ==CU_MILIMOLAR: #mM
            C = self.C_spinner.get_value() / 1000.0
        else: #mg/ml
            MW = self.MW_spinner.get_value()
            if MW != 0.0:
                C = self.C_spinner.get_value() / MW
            else:
                C = 0.0
        LP = self.LP_spinner.get_value()
        Rn = self.Rn_spinner.get_value()
        FC_0 = 10*LP*C*Rn
        if FC_0 != 0:
            self.correction_factor = 1.0/FC_0
        else:
            self.correction_factor = 0.0
        return self.correction_factor

    def _c_units_changed_cb(self, widget):        
        cu = self.c_units_combo.get_active()        
        if cu ==CU_MICROMOLAR:
            text = self.c_text % "uM"
            self.C_spinner.set_increments(0.1, 1.0)
        elif cu ==CU_MILIMOLAR:
            text = self.c_text % "mM"
            self.C_spinner.set_increments(0.01, 0.1)
        else:
            text = self.c_text % "mg/ml"
            self.C_spinner.set_increments(0.01, 0.1)
        self.C_label.set_text(text)
        self._update_factor_cb(widget)

    def _copy_to_clipboard_cb(self, widget):
        clipboard = gtk.Clipboard()
        clipboard.set_text("%f" % self._calculate_fc())

    def _update_factor_cb(self, widget):
        self.factor_entry.set_text("%f" % self._calculate_fc())

    def _configure_widgets(self, protein_info):
        self.LP_spinner.set_value(protein_info.default_light_path)
        self.C_spinner.set_value(protein_info.default_concentration)
        self.c_units_combo.set_active(protein_info.get_c_units())
        self._c_units_changed_cb(self.c_units_combo)
        self.MW_spinner.set_value(protein_info.molecular_weight)
        self.Rn_spinner.set_value(protein_info.residue_number)

        self._update_factor_cb(self)

        self.c_units_combo.connect("changed", self._c_units_changed_cb)
        self.LP_spinner.connect("value-changed", self._update_factor_cb )
        self.C_spinner.connect("value-changed", self._update_factor_cb )
        self.MW_spinner.connect("value-changed", self._update_factor_cb )
        self.Rn_spinner.connect("value-changed", self._update_factor_cb )
        
    def _create_widgets(self):
        def create_label(label):
            l = gtk.Label(label)
            l.set_alignment(0,0.5)
            l.set_use_markup(True)
            return l
        self.LP_spinner = gtk.SpinButton()  
        self.LP_spinner.set_range(0.0,10.0)
        self.LP_spinner.set_digits(2)
        self.LP_spinner.set_increments(0.01, 0.1)
        self.C_label = create_label(_("Concentration (mg/ml):"))
        self.C_spinner = gtk.SpinButton()
        self.C_spinner.set_range(0.0,50.0)
        self.C_spinner.set_digits(4)
        self.C_spinner.set_increments(0.01, 0.1)
        self.MW_spinner = gtk.SpinButton()
        self.MW_spinner.set_range(1.0,1000000000000.0)
        self.MW_spinner.set_digits(2)
        self.MW_spinner.set_increments(10.0, 100.0)
        self.Rn_spinner = gtk.SpinButton()
        self.Rn_spinner.set_range(1.0,1000000000000.0)
        self.Rn_spinner.set_digits(0)
        self.Rn_spinner.set_increments(1.0, 10.0)
        self.factor_entry = gtk.Entry()
        self.factor_entry.props.editable = False
        self.factor_entry.set_text("%f" % 0.0)
        self.c_units_list = gtk.ListStore(str)
        self.c_units_list.append(["m:v (mg/ml)"])
        self.c_units_list.append(["micromolar"])
        self.c_units_list.append(["milimolar"])
        cell = gtk.CellRendererText()
        self.c_units_combo = gtk.ComboBox(self.c_units_list)
        self.c_units_combo.pack_start(cell, True)
        self.c_units_combo.add_attribute(cell, 'text', 0)
        self.c_units_combo.set_active(0)

        self.copy_to_clipboard_btn = gtk.Button(stock=gtk.STOCK_COPY)
        self.copy_to_clipboard_btn.connect("clicked", self._copy_to_clipboard_cb)        

        table = gtk.Table(6,2)
        table.set_row_spacings(3)
        table.set_col_spacings(3)
        table.attach(create_label(_("Light path (cm):")),
                     0,1,0,1, gtk.FILL, gtk.EXPAND|gtk.FILL)
        table.attach(self.LP_spinner,
                     1,2,0,1, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL)
        table.attach(self.c_units_combo,
                     0,2,1,2, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL)
        table.attach(self.C_label,
                     0,1,2,3, gtk.FILL, gtk.EXPAND|gtk.FILL) 
        table.attach(self.C_spinner,
                     1,2,2,3, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL)
        table.attach(create_label(_("Molecular weight (g/mol):")),
                     0,1,3,4, gtk.FILL, gtk.EXPAND|gtk.FILL)
        table.attach(self.MW_spinner,
                     1,2,3,4, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL)
        table.attach(create_label(_("Residue number:")),
                     0,1,4,5, gtk.FILL, gtk.EXPAND|gtk.FILL) 
        table.attach(self.Rn_spinner,
                     1,2,4,5, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL)
        table.attach(create_label(_("<b>Correction factor:</b>")),
                     0,1,5,6, gtk.FILL, gtk.EXPAND|gtk.FILL,0,5)
        table.attach(self.factor_entry,
                     1,2,5,6, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL,0,5)
        self.vbox.pack_start(table, False, False, 4)
        self.action_area.pack_end(self.copy_to_clipboard_btn, False, False, 0)
        self.set_border_width(2)
        self.show_all()

if __name__=="__main__":
    w = CDCorrectionFactorCalculator()
    w.run()


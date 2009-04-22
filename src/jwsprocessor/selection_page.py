#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import pygtk
pygtk.require("2.0")
import gtk
import gobject
import os, sys
from tools import SpectraDB, _
from smoothing_selection import ShowSpectrumPanel
from jws_filechooser import JwsFileChooserDialog

class SelectionPage(gtk.HPaned):
    def __init__(self, assistant, current_folder=os.getcwd()):
        self.assistant = assistant
        self.removing_multi = False
        self.create_widgets()

        # El objeto SpectraDB nos asegura que no hayan duplicados en la lista de
        # espectros. Además almacena las cabeceras de cada espectro listado.
        # NOTA IMPORTANTE: la lista de espectros tiene un TreeModelSort que
        # del spectra_list, el ListStore que maneja spectra_db. Por tanto, antes
        # de pasar cualquier path ó iter a spectra_db hay que convertirlo del
        # TreeSortModel al ListStore.
        self.spectra_db = SpectraDB(self.spectra_list)
        self.current_folder = current_folder

    def create_widgets(self):
        gtk.HPaned.__init__(self)

        self.create_spectralist()
        self.sl_add_action = gtk.Action("sl_add", 
                                        None, 
                                        _("Add spectra"), 
                                        gtk.STOCK_ADD)
        self.sl_add_action.connect("activate", self.sl_add_button_cb)

        self.sl_remove_action = gtk.Action("sl_remove", 
                                            None, 
                                            _("Eliminate selected spectra"), 
                                            gtk.STOCK_REMOVE)
        self.sl_remove_action.connect("activate", self.sl_remove_button_cb)
        self.sl_remove_action.set_sensitive(False)

        self.dil_paste_action = gtk.Action( "dil_paste", 
                                            None, 
                                            _("Paste dilution data"), 
                                            gtk.STOCK_PASTE)
        self.dil_paste_action.connect("activate", self._request_targets)
        self.dil_paste_action.set_sensitive(False)

        self.dil_reset_action = gtk.Action("dil_reset", 
                                            None, 
                                            _("Erase dilution data"), 
                                            gtk.STOCK_CLEAR)
        self.dil_reset_action.connect("activate", self.reset_dilution_button_cb) 

        self.show_preview_action = gtk.ToggleAction("show_preview_action", 
                                    _("Preview"), 
                                    _("Show a plot of the selected spectrum"),
                                    gtk.STOCK_PRINT_PREVIEW)
        self.show_preview_action.connect("toggled", self._show_preview_toggle_cb)

        dil_menu = gtk.Menu()
        dil_menu.insert(self.dil_paste_action.create_menu_item(),-1)  
        dil_menu.insert(self.dil_reset_action.create_menu_item(),-1) 
        dil_toolmenu = gtk.MenuToolButton( \
                icon_widget = gtk.image_new_from_stock(gtk.STOCK_PASTE, 
                                                       gtk.ICON_SIZE_SMALL_TOOLBAR),
                label=_("Dilution data"))
        dil_toolmenu.set_menu(dil_menu)
        dil_toolmenu.connect("clicked", self.dilution_menutoolbutton_cb)
        dil_toolmenu.set_tooltip(gtk.Tooltips(), _("Paste dilution factors"))
        dil_toolmenu.set_is_important(True)
        toolbar = gtk.Toolbar()
        toolbar.insert(self.sl_add_action.create_tool_item(),-1)
        toolbar.insert(self.sl_remove_action.create_tool_item(),-1)     
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        toolbar.insert(dil_toolmenu,-1)
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        toolbar.insert(self.show_preview_action.create_tool_item(), -1)
        toolbar.set_style(gtk.TOOLBAR_BOTH_HORIZ)
        tv_vbox = gtk.VBox()
        tv_vbox.pack_start(toolbar, False, False, 4)
        tv_vbox.pack_start(self.spectra_scroll, True, True, 0)
        tv_frame = gtk.Frame(_("Spectra to be processed:"))
        tv_frame.add(tv_vbox)

        self.spectrum_panel = ShowSpectrumPanel()                      
        self.pack1(tv_frame, True, True)

        self.clipboard = gtk.clipboard_get(selection="CLIPBOARD")

    def _show_preview_toggle_cb(self, widget,data=None):
        if self.show_preview_action.props.active:
            self._spectra_sel_changed_cb(self.spectra_sel)
        else:
            if self.spectrum_panel.props.visible:
                self.spectrum_panel.hide()
            
    def dilution_menutoolbutton_cb(self, widget, data=None):
        if self.dil_paste_action.props.sensitive:
            self._request_targets(widget)

    def reset_dilution_button_cb(self, widget, data=None):
        _iter = self.spectra_list.get_iter_first()
        while _iter is not None:
            self.spectra_list.set_value(_iter, 7, 1.0)
            _iter = self.spectra_list.iter_next(_iter)
        
    def _request_targets(self, widget, data=None):
        self.clipboard.request_text(self._request_text_cb)
        return True

    def _request_text_cb(self, clipboard, text, user_data = None):
        if text == "": return
        # Primero romprer los datos en una lista. Nota: hay que comprobar que 
        # los datos estén separados por "\n", a veces están separados por \r ó 
        # por \n\r
        if "\n\r" in text:
            datalist = text.split("\n\r")       
        elif "\n" in text:
            datalist = text.split("\n")
        elif "\r" in text:
            datalist = text.split("\r")
        else:
            datalist = [text]       
        # Comprobar que los datos a pegar sean válidos (que contengan un float)
        nlist = []
        for elem in datalist:
            if "\t" in elem:
                elem_s = elem.split("\t")[0]
            else:
                elem_s = elem
            try:
                n = float(elem_s)
            except:
                pass
            else:
                nlist.append(n)
        # Meter los datos en la columna correspondiente, a partir de la fila
        # que esté seleccionada:
        if len(nlist)>0:            
            (model, piter_list) = self.spectra_sel.get_selected_rows()
            start_path = min(piter_list)
            _iter = model.get_iter(start_path)
            while (_iter is not None) and (len(nlist) > 0):
                value = nlist.pop(0)
                model.set_value(_iter, 7, value)
                _iter = model.iter_next(_iter) 

    def create_spectralist(self):
        def new_column(name, data_attr, column_id, editable=False):
            col = gtk.TreeViewColumn(name)
            col.set_resizable(True)
            col.set_clickable(True)
            self.spectra_view.append_column(col)
            #identificación de cada columna a la hora de ordenar:
            col.set_sort_column_id(column_id)
            
            cell = gtk.CellRendererText()
            cell.set_property("editable", editable)
            col.pack_start(cell, True)
            col.add_attribute(cell, data_attr, column_id)            
            return col, cell
        
        # [0=nombre (str),          1=nº puntos (int),      2=lamda inicial (float),
        #  3=lambda final (float),  4=data pitch (float),   5=ruta (float), 
        #  6=nombre_completo (str), 7=dilución (float)      ]        
        self.spectra_list = gtk.ListStore(str, int, float, float, float, str, str, float)
        self.spectra_view = gtk.TreeView(self.spectra_list)

        (col1, cell1) = new_column(_("Name"), "text", 0)
        (dilution_column, dilution_cell) = new_column(_("Dilution"), "text", 7, 
                                                      editable=True)
        (col2, cell2) = new_column(_("Point no."), "text", 1)
        (col3, cell3) = new_column(_("Initial λ"), "text", 2)
        (col4, cell4) = new_column(_("Final λ"), "text", 3)
        (col5, cell5) = new_column(_("Data pitch"), "text", 4)
        (col6, cell6) = new_column(_("File path"), "text", 5)
        dilution_cell.connect("edited", self._dilution_edited_cb)
        self.spectra_view.props.reorderable = True
        self.spectra_view.set_border_width(5)
        
        self.spectra_sel = self.spectra_view.get_selection()
        self.spectra_sel.set_mode(gtk.SELECTION_MULTIPLE)
        self.spectra_sel.connect("changed", self._spectra_sel_changed_cb)
                
        self.spectra_scroll = gtk.ScrolledWindow()
        self.spectra_scroll.set_policy( gtk.POLICY_AUTOMATIC,
                                        gtk.POLICY_AUTOMATIC )
        self.spectra_scroll.add(self.spectra_view)                 

        self.spectra_list.connect("row-inserted", self._sl_rowinserted_cb)
        self.spectra_list.connect("row-deleted", self._sl_rowdeleted_cb)
        
    def _spectra_sel_changed_cb(self, widget, data=None):
        (model, piter_list) = widget.get_selected_rows()
        #activar todos los widgets que dependan de que exita algo seleccionado:
        something_selected = len(piter_list) > 0
        self.sl_remove_action.set_sensitive(something_selected)
        self.dil_paste_action.set_sensitive(something_selected)
        if self.show_preview_action.props.active:
            if something_selected and (not self.removing_multi):
                fn = model.get_value(model.get_iter(piter_list[0]), 6).decode('utf-8')
                if fn in self.spectra_db:                
                    self.spectrum_panel.show_spectrum_file(fn)
                    if not self.get_child2():
                        self.pack2(self.spectrum_panel, True, True)
                    self.spectrum_panel.show()
                else:
                    raise Exception, \
'SpectraSelectionWidnow.sv_row_activated_cb(): Value from treeview list not in\
spectra database'
            else:
                self.spectrum_panel.hide()

    def _blank_entry_changed_cb(self, entry, data=None):
        self.__check_model_empty(self.spectra_list)
        
    def _sl_rowinserted_cb(self, model, path, iter, data=None):
        self.__check_model_empty(model)
        
    def _sl_rowdeleted_cb(self, model, path, data=None):
        self.__check_model_empty(model)

    def __check_model_empty(self, model):
        model_empty = model.get_iter_first() is None
        #self.set_response_sensitive(gtk.RESPONSE_ACCEPT, not model_empty)
        self.assistant.set_page_complete(self, not model_empty)                

    def _dilution_edited_cb(self, cell, path, new_text, data=None):
        try:
            new_value = float(new_text)
        except:
            new_value = None
        if new_value != None:
            _iter = self.spectra_list.get_iter(path)
            self.spectra_list.set_value(_iter, 7, new_value)
              
    def sl_add_button_cb(self, button, user_data=None):
        fs_dialog = JwsFileChooserDialog( parent= self.assistant,
                                          current_folder = self.current_folder,
                                          title=_("Open spectra..."))
        response = fs_dialog.run()
        if response == gtk.RESPONSE_OK:
            #En windows hay que recodificar los nombres de archivo!!
            fns = [fn.decode('utf-8') for fn in fs_dialog.get_filenames()]
        else:
            fns = None
        if fns:
            self.spectra_db.append_files(fns)
            self.current_folder = fs_dialog.get_current_folder().decode('utf-8')
        fs_dialog.destroy()

    def sl_remove_button_cb(self, button, user_data=None):
        (model, path_list) = self.spectra_sel.get_selected_rows()
        if len(path_list)>1:
            self.removing_multi = True
        self.spectra_db.remove_pathlist(path_list)
        self.removing_multi = False

    def _namecells_datafunc(self, column, cell, model, iter, user_data=None):
        path = model.get_value(iter, 0).decode('utf-8')
        if path:
            # head = (path); tail = (nombre de archivo)
            (head, tail) = os.path.split(path)
            cell.set_property('text', tail)

    def _pathcells_datafunc(self, column, cell, model, iter, user_data=None):
        path = model.get_value(iter, 0).decode('utf-8')
        if path:
            (head, tail) = os.path.split(path)
            cell.set_property('text', head)

    def get_ordered_data(self):
        ''' Devuelve una lista con los espectros de la lista de espectros
            ordenados.
        '''
        _iter = self.spectra_list.get_iter_first()
        result = []
        while _iter is not None:
            fn = self.spectra_list.get_value(_iter, 6).decode('utf-8')
            dilution = self.spectra_list.get_value(_iter, 7)
            result.append((fn, dilution))
            _iter = self.spectra_list.iter_next(_iter)
        return result
    
    def get_ordered_list(self):
        ''' Devuelve una lista con los espectros de la lista de espectros
            ordenados.
        '''
        _iter = self.spectra_list.get_iter_first()
        result = []
        while _iter is not None:
            result.append(self.spectra_list.get_value(_iter, 6).decode('utf-8'))
            _iter = self.spectra_list.iter_next(_iter)
        return result

    def get_selected_spectra(self):
        (model, path_list) = self.spectra_sel.get_selected_rows()
        selected_spectra = []
        for path in path_list:
            selected_spectra.append(model.get_value(model.get_iter(path),6).decode('utf-8'))
        return selected_spectra

    def reset(self):
        self.spectra_list.clear()
        del self.spectra_db
        self.spectra_db = SpectraDB(self.spectra_list)

if __name__=="__main__":
  ssd = SelectionDialog()
  ssd.run()

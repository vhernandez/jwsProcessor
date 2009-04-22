#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
TO DO:
- Guardar las opciones usadas anteriormente
- Hacer una base de datos sobre proteínas, con su peso molecular y su número
  de residuos, para calcular rápidamente el factor de corrección.
"""
import pygtk
pygtk.require("2.0")
import gtk
import gobject
import os
import gettext
from def_config import *
from selection_page import SelectionPage
from save_options_page import SaveOptionsPage
from summary_page import SummaryPage
from process_form import ProcessForm
from options_page import OptionsPage
from tools import ask_yesno, ProcessOptions, _
from jws_processing import *

class JwsAssistant(gtk.Assistant):

    def __init__(self):
        self.blank_msg = \
_("""The selected blank is among the files to be processed. 
Do you really want to continue?""")

        self.heterogeneus_xvalues_msg = \
_("""No every file has the same data pitch o data does
not always begin at the same wavelength. Do you want to
save data with a column for X values for each spectrum?
""")

        self.intro_msg = \
_("""Welcome to jwsProcessor.

This assistant consists on four steps:
#1 Select the .jws files to be processed
#2 Choose the processing options
#3 Process of the files
#4 Save the results
""")

        # Set Internal variables
        self.options = ProcessOptions()
        self.spc_list = []
        self.processed_files = []
        self.processed_list = []
        self.success_count = 0
        self.current_folder = config.get(CFGFILE_SECTION, LAST_DIR_STR)
        self.__no_files_processed = False

        self._create_widgets()

    def _create_widgets(self):
        gtk.Assistant.__init__(self)
        # Page 0
        ip = gtk.Label(self.intro_msg)
        self.append_page(ip)       
        self.set_page_type(ip, gtk.ASSISTANT_PAGE_INTRO)
        self.set_page_title(ip, _("jwsProcess assistant"))
        self.set_page_complete(ip, True)
        self.intro_page = ip
        # Page 1
        sp = SelectionPage(self, self.current_folder)
        self.append_page(sp)
        self.set_page_type(sp, gtk.ASSISTANT_PAGE_CONTENT)
        self.set_page_title(sp, _("#1 - Select spectra"))
        self.set_page_complete(sp, False)
        self.selection_page = sp
        # Page 2
        op = OptionsPage(options=self.options,
                         current_folder = sp.current_folder,
                         assistant=self)
        self.append_page(op)              
        self.set_page_type(op, gtk.ASSISTANT_PAGE_CONFIRM)
        self.set_page_title(op, _("#2 - Processing options"))
        self.set_page_complete(op, False)
        self.options_page = op
        # Page 3
        fp = SummaryPage(self)
        self.append_page(fp)
        self.set_page_title(fp, _("#3 - Results"))
        self.set_page_complete(fp, False)
        self.summary_page = fp
        # Page 4
        sop = SaveOptionsPage(self)
        self.append_page(sop)
        self.set_page_type(sop, gtk.ASSISTANT_PAGE_CONFIRM)
        self.set_page_title(sop, _("#4 - Save results as..."))
        self.set_page_complete(sop, True)
        self.save_options_page = sop
        # Page 5
        fp = gtk.Label(_("Saving files..."))
        self.append_page(fp)
        self.set_page_type(fp, gtk.ASSISTANT_PAGE_SUMMARY)
        self.set_page_title(fp, _("Summary"))
        self.set_page_complete(fp, False)
        self.final_page = fp
        # Restart assistant button
        self.restart_button = gtk.Button(_("Start again"))
        self.restart_button.set_image(gtk.image_new_from_stock(gtk.STOCK_GOTO_FIRST,
                                                               gtk.ICON_SIZE_BUTTON) )
        self.restart_button.connect("clicked", self._restart_clicked_cb)
        self.restart_button.show_all()
        # Configure window
        self.set_title("jwsProcess")
        self.set_forward_page_func(self._fwd_page_func)
        self.show_all()
        self.connect("delete-event", self._close_cb)
        self.connect("prepare", self._prepare_cb)
        self.connect("apply", self._apply_cb)
        self.connect("close", self._close_cb)
        self.connect("cancel", self._close_cb)
        
    def _close_cb(self, widget, event=None):
        config.set(CFGFILE_SECTION, LAST_DIR_STR, self.current_folder)
        gtk.main_quit()

    def _restart_clicked_cb(self, widget):
        self.selection_page.reset()
        self.remove_action_widget(self.restart_button)
        self.set_current_page(0)

    def _apply_cb(self, widget):
        """ Este callback es llamado cuando el usuario ha pulsado el botón
            "Aplicar" en una página de tipo ASSISTANT_PAGE_CONFIRM, pero siempre
            una vez que se ha mostrado la página siguiente a dicha página.
            En este wizzard tenemos 2 páginas de confirmación, la página 2 en la 
            que se seleccionan las opciones de procesado y la página 4 en la que
            se seleccionan las opciones de guardado. Por tanto en esta página se 
            llevarán a cabo:
            #1 El procesado de los datos (cuando página actual == 3)
            #2 El guardado de los datos procesados (cuando la página actual==5)            
        """
        page = self.get_nth_page(self.get_current_page()) 
        print "apply_cb, current_page=", page #debug
        if page == self.summary_page:
            # Check if blank is included in spectra list(?)
            # if it is, then allow the user to re-run the options dialo
            self.options = self.options_page.get_options()
            if self.options.subtract_blank:
                if self.options.blank_fn in self.selection_page.spectra_db:
                    if ask_yesno(title=self.blank_msg, parent=self)!=gtk.RESPONSE_YES:
                        self.set_current_page(2)
                        return
            # Process spectra
            self.spc_list = self.selection_page.get_ordered_data()
            process_form = ProcessForm()
            processor = JwsProcessor(process_form)         
            results = processor.process_files(options=self.options, 
                                              spectra_list=self.spc_list)
            if results:
                (self.processed_files, self.processed_list, self.success_count) = results            
            else:
                self.success_count = 0
            # Show the results in self.summary_page
            info_buffer = processor.report_buffer
            process_form.destroy()
            if self.success_count > 0:
                mensaje = _('Successfully processed files: %(#)d out of %(##)d.') \
                        % {'#': self.success_count, '##':len(self.spc_list)}
                image_type = gtk.STOCK_DIALOG_INFO                
            else:
                mensaje = _("Spectra could not be processed!")
                image_type = gtk.STOCK_DIALOG_ERROR
                self.__no_files_processed = True
            self.summary_page.set_message(mensaje, info_buffer, image_type)
            self.set_page_complete(self.summary_page, True)            

        elif page == self.final_page:
            # Save files
            print self.save_options_page.get_option() #debug
            save_option = self.save_options_page.get_option()
            column_headers_option = self.save_options_page.get_column_headers_option()
            if save_option != self.save_options_page.SO_DONT_SAVE:
                files_saved = self._save_files( save_option, 
                                                column_headers_option, 
                                                self.processed_list, 
                                                self.processed_files, 
                                                self.success_count)
                print "Files saved = ", files_saved #debug
                if files_saved is None:
                    self.set_current_page(4)
                else:
                    msg = _("Successfully saved files: %(#)d out of %(##)d") % \
                                {'#':files_saved, '##':len(self.processed_list)}
                    self.final_page.set_text(msg)
            else:
                self.final_page.set_text(_("Results have not been saved."))


    def _fwd_page_func(self, current_page):
        return_val = current_page+1
        page = self.get_nth_page(current_page)        
        if page == self.summary_page:
            if self.__no_files_processed:
                return_val = 5
        return return_val

    def _prepare_cb(self, assistant, page):        
        if page == self.options_page:
            self.current_folder = self.selection_page.current_folder
            self.options_page.current_folder = self.selection_page.current_folder
            self.options_page.check_blank_options()            
        elif page == self.summary_page:
            self.current_folder = self.options_page.current_folder
        elif page == self.save_options_page:
            pass
        elif page == self.final_page:
            if self.__no_files_processed:
                self.final_page.set_text(_("No file could be processed."))
            self.add_action_widget(self.restart_button)
 
    def _save_files(self, save_option, write_column_headers, processed_list, 
                    processed_files, success_count):
        """ 
        Parámetros:
            - save_option: de qué forma guardar los espectros
            - write_column_headers: incluir o no el nombre de cada espectro en
              el archivo
            - processed_list, processed_files: listas con los datos procesados
              y con el nombre de los archivos originales respectivamente
            - success_count: es el número de archivos que se deben guardar.
            
        Devuelve el número de espectros guardados, o None si no se han
        guardado los esfpectros debido al usuario.
        Si se devuelve None se debería volver a preguntar al usuario si desea
        guardar los resultados.
        """
        # 1. Hacer que el usuario escoja en qué fichero o en qué carpeta quiere        
        # guardar los resultados
        if (save_option==self.save_options_page.SO_ONEFILE_ONEX) or \
           (save_option==self.save_options_page.SO_ONEFILE_MULTIPLEX):
            continuar = True
            while continuar:
                output_fn = self._choose_file_to_save()
                continuar = False
                # Salir si el usuario declina elegir un archivo:
                if not output_fn:                    
                    return None
                # Comprobar si el archivo existe, preguntar si sobreescribirlo:
                elif os.path.exists(output_fn):                    
                    mensaje=_("The file %s already exist, do you want to overwrite it?") \
                            % os.path.split(output_fn)[1]
                    if ask_yesno( title=mensaje ) != gtk.RESPONSE_YES:
                        continuar = True
            self.current_folder = os.path.split(output_fn)[0] ## update current folder!!
        elif (save_option==self.save_options_page.SO_MULTIPLE_FILES):
            output_folder = self._choose_folder_to_save()
            # Salir si el usuario declina elegir una carpeta:
            if not output_folder:
                return None
            self.current_folder = output_folder ## update current folder!!
       
        # 2. Salvar los resultados según la opción elegida por el usuario
        if (save_option==self.save_options_page.SO_ONEFILE_ONEX):
            # Comprobar si todos los ficheros tienen el mismo eje x...
            results = check_homogeneity(processed_files)
            if results:
                (startx, xpitch) = results
                save_to_one_file_onex(processed_files, processed_list,
                                      startx, xpitch,
                                      output_fn, write_column_headers)
                # Asumir que hemos guardado todos los espectros:
                return_value = success_count
            # ... si no lo tienen, entonces quizá el usuario quiera guardar los
            # datos del eje x de cada expectro:
            else:            
                if ask_yesno(title=heterogeneus_xdata_msg) == gtk.RESPONSE_YES:
                    save_to_one_file_multiplex(processed_files, processed_list,
                                               output_fn)
                    # Asumir que hemos guardado todos los espectros:
                    return_value = success_count
                else:
                    return_value = None
        elif (save_option==self.save_options_page.SO_ONEFILE_MULTIPLEX):
            save_to_one_file_multiplex(processed_files, processed_list,
                                       output_fn)
            # Asumir que hemos guardado todos los espectros:
            return_value = success_count
        elif (save_option==self.save_options_page.SO_MULTIPLE_FILES):
            return_value = save_to_separate_files(processed_files, output_folder)
        else:
            return_value = None            
        return return_value            

    def _choose_file_to_save(self):
        return_value = None
        buttons = ( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
                    gtk.STOCK_SAVE, gtk.RESPONSE_OK )
        fs_dialog = gtk.FileChooserDialog( title=_("Save results as..."),
                                           action= gtk.FILE_CHOOSER_ACTION_SAVE,
                                           buttons= buttons)
        fs_dialog.add_filter(ff_txt)
        fs_dialog.set_select_multiple(False)
        fs_dialog.set_current_folder(self.selection_page.current_folder)
        response = fs_dialog.run()
        if response == gtk.RESPONSE_OK:
            fn = fs_dialog.get_filename().decode('utf-8')
            self.selection_page.current_folder = fs_dialog.get_current_folder().decode('utf-8')
            return_value = fn
        fs_dialog.destroy()       
        return return_value

    def _choose_folder_to_save(self):
        return_value = None
        buttons = ( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
                    gtk.STOCK_SAVE, gtk.RESPONSE_OK )
        fs_dialog = gtk.FileChooserDialog( title=_("Select a folder"),
                                           action= gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                           buttons= buttons )
        fs_dialog.set_select_multiple(False)
        fs_dialog.set_current_folder(self.selection_page.current_folder)
        response = fs_dialog.run()
        if response == gtk.RESPONSE_OK:
            folder = fs_dialog.get_filename().decode('utf-8')
            self.selection_page.current_folder = fs_dialog.get_current_folder().decode('utf-8')
            return_value = folder
        fs_dialog.destroy()
        return return_value

def main(debug=False):
    
    localedir = localepath()

    gettext.bindtextdomain('jwsprocessor', localedir)
    gettext.textdomain('jwsprocessor')

    cfgFile = config_load_validate()

    # Load the icon for the window; here we just load one, default icon
    gtk.window_set_default_icon_from_file( imagepath("jwsprocessor.svg") )

    app_window = JwsAssistant()
    gtk.main()
    
    config_save(cfgFile)
    if debug:
        printConfigParser() ##debug

if __name__=="__main__":    
    main()

#!/usr/bin/env python
# -*- coding: UTF8 -*-
import pygtk
pygtk.require("2.0")
import gtk
import os
import jwslib
import gettext
from numpy.oldnumeric import array, arange, Float

#gettext
_ = gettext.gettext

# Funciones --------------------------------------------------------------------
def wait_till_refresh():
    '''
    Waits until all pending events are completed. This is to allow the GUI
    to be refreshed when we are doin a time-intensive task.
    '''
    while gtk.events_pending():
        gtk.main_iteration()


def ask_yesno(title="Yes or no?", parent=None):
    ''' Createx a Yes or No dialog and returns the answer given by the user.'''
    yesno_dlg = gtk.MessageDialog(parent, gtk.DIALOG_MODAL,
                gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                title)
    respuesta = yesno_dlg.run()
    wait_till_refresh()
    yesno_dlg.destroy()
    return respuesta                                    


def show_error_message(title="Error", parent=None):
    ''' Shows and error message dialog '''
    dlg = gtk.MessageDialog(parent, gtk.DIALOG_MODAL,
                            gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                            title)
    dlg.run()
    wait_till_refresh()
    dlg.destroy()

def show_info_message(title="Information", parent=None):
    ''' Shows an information message dialog '''
    dlg = gtk.MessageDialog(parent, gtk.DIALOG_MODAL,
                            gtk.MESSAGE_INFORMATION, gtk.BUTTONS_OK,
                            title)
    dlg.run()
    wait_till_refresh()
    dlg.destroy()

def find_value_in_model(model, column_id, target_value):
    return_iter = None
    _iter = model.get_iter_first()
    while _iter:
        value = model.get_value(_iter, column_id).decode('utf-8')
        if value == target_value:
            return_iter = _iter
            _iter = None #exit loop
        else:
            _iter = model.iter_next(_iter)
    return return_iter


# Clases -----------------------------------------------------------------------    
class ProcessOptions:
    def __init__(self, subtract_blank=True, blank_fn=None,
                 subtract260=True, correct_dilution=False,
                 smoothing=True, smoothing_type = "mm", m=25, p=3,
                 correct=False, cf=1.0 ):
        self.subtract_blank = subtract_blank
        self.subtract260 = subtract260
        self.smoothing = smoothing
        self.smoothing_type = smoothing_type
        self.m = self.__clamp_m(m)
        self.p = self.__clamp_p(p)
        self.blank_fn = blank_fn
        self.correct = correct
        self.correction_factor = cf
        self.correct_dilution = correct_dilution

    def __clamp_p(self, p):
        if p>6:
            p=6
        elif p<2:
            p=2
        return p

    def __clamp_m(self, m):
        if m>25:
            m=25
        elif m<5:
            m=5
        if (m%2) != 1:
            m+=1
        return m

    def set_clamped_m(self, m):
        self.m = self.__clamp_m(m)

    def get_clamped_m(self):
        self.set_clamped_m(self.m)
        return self.m
        
    def set_clamped_p(self, p):
        self.p = self.__clamp_p(p)

    def get_clamped_p(self):
        self.set_clamped_p(self.p)
        return self.p


class SpectraDB:
    def __init__(self, model):
        self.model = model
        self.path_set = set()
        self.headers = {}

    def append_files(self, file_list):
        ''' Try to add files in file_list to the database.
        '''        
        for fn in file_list:
            self.append_file(fn)           
            
    def append_file(self, fn):
        ''' Returns file's header if the file was appended succesfully
            or else retuns None.
        '''
        return_value = False
        if not fn in self.path_set:
            header = jwslib.read_header(fn)
            if header:
                # head = (path); tail = (nombre de archivo)
                (head, tail) = os.path.split(fn)
                self.path_set.add(fn)
                self.model.append([ tail, 
                                    header.point_number, 
                                    header.x_for_first_point,
                                    header.x_for_last_point,
                                    header.x_increment,
                                    head,
                                    fn,                                    
                                    1.0] )
                self.headers[fn] = header                
        return return_value  
                        
    def remove_files(self, file_list):
        for fn in file_list:
            self.remove_file(fn)
    
    def remove_file(self, fn):
        if fn in self.path_set: 
            self.path_set.remove(fn)
            del self.headers[fn]
            
        value_iter = find_value_in_model(self.model, 6, fn)
        if value_iter:
            self.model.remove(value_iter)

    def remove_pathlist(self, path_list):        
        tree_row_references = [gtk.TreeRowReference(self.model,path) for path in path_list]
        for tr in tree_row_references:
            path = tr.get_path()
            value = self.model.get_value(self.model.get_iter(path),6).decode('utf-8')
            self.model.remove(self.model.get_iter(path))
            self.path_set.remove(value)
            del self.headers[value]

    def __contains__(self, item):
        return item in self.path_set
    has_file = __contains__

    def __len__(self):
        return len(self.path_set)



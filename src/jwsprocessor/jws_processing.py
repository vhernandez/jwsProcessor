#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import pygtk
pygtk.require("2.0")
import gtk
import os
#from Numeric import array, arange, Float, multiply, subtract
from numpy import array, arange, multiply, subtract, float32
from random import choice
import jwslib
import pysmoothing
from tools import _

def check_homogeneity(processed_files):
    """ Checks that x_increment (data pith) and x_for_first_point
        is the same for all the spectrum in the processed_files dict
        If they are the same it returns the tuple (startx, xpitch) else
        it returns False.
    """
    results0 = choice(processed_files.values())
    (header0, channels0) = results0
    startx = header0.x_for_first_point
    xpitch = header0.x_increment
    startx_equal = True
    xpitch_equal = True
    for results in processed_files.itervalues():
        (header, channels) = results
        if header.x_for_first_point != startx:
            startx_equal = False
            break
        if header.x_for_first_point != startx:
            xpitch_equal = False
            break
    if not (startx_equal and xpitch_equal):
        return False
    else:
        return (startx, xpitch)

def save_to_one_file_onex(processed_files, processed_list, startx, xpitch, 
                          output_fn, write_column_headers = True):
    """ Save to one file, only one x column:
        processed_files = dictionary, key is the filename and values are
                          header and channel_data.
        processed_list = an ordered list of the filenames (the keys of
                         processed_files), so the order of the columns in the
                         the output file can be controlled
    """
    columns = []
    maxlen = 0
    maxlastx = startx
    minlastx = startx
    for fn in processed_list:
        (header, channels) = processed_files[fn]
        # Y Data - Only save one channel!!            
        (head, tail) = os.path.split(fn) # head=path; tail=nombre arch.
        ydata = [tail] + [channels[0][i] for i in xrange(header.point_number)]
        columns.append(ydata)
        if header.point_number > maxlen:
            maxlen = header.point_number
        if header.x_for_last_point > maxlastx:
            maxlastx = header.x_for_last_point
        if header.x_for_last_point < minlastx:
            minlastx = header.x_for_last_point
    # X Data
    if xpitch < 0:  
        endx = minlastx + xpitch
    else:
        endx = maxlastx + xpitch
    xdata = ["X"] + list( arange(startx, endx, xpitch) )
    columns.insert(0, xdata)
    
    f = open(output_fn, "w")
    # escribir nombre de cada columna
    if write_column_headers:
        for col in columns:
            f.write("%s\t" % col[0])
        f.write("\n")
    # escribir datos
    for i in xrange(1,maxlen+1):
        for col in columns:
            if i<len(col):
                f.write("%g" % col[i])
            f.write("\t")
        f.write("\n")
    f.close()
    
def save_to_one_file_multiplex(processed_files, processed_list, output_fn):
    # Save to one file, multiple x columns:
    columns = []
    maxlen = 0
    for fn in processed_list:
        (header, channels) = processed_files[fn]
        # X Data
        xdata = list(arange(header.x_for_first_point,                    #start
                            header.x_for_last_point+header.x_increment,  #end+incr.
                            header.x_increment))                         #increment
        columns.append(xdata)
        # Y Data - Only save one channel!!
        ydata = [channels[0][i] for i in xrange(header.point_number)]
        columns.append(ydata)
        if header.point_number > maxlen:
            maxlen = header.point_number

    f = open(output_fn, "w")
    for i in xrange(maxlen):
        for col in columns:
            if i<len(col):
                f.write("%g" % col[i])
            f.write("\t")
        f.write("\n")
    f.close()

def save_to_separate_files(processed_files, output_folder=None):
    # Save to separate files:
    saved_counter = 0
    for fn, results in processed_files.iteritems():            
        (header, channels) = results
        if output_folder:
            (head, tail) = os.path.split(fn) # head=path; tail=nombre arch.
            if tail[-4:] == ".jws":
                fn = tail[:-4] + ".txt"
            else:
                fn = tail + ".txt"
            output_fn = os.path.join(output_folder, fn)
        else:
            output_fn = fn[:-4]+".txt"
        wresults = jwslib.dump_channel_data(output_fn, header, channels)
        error = True
        if wresults[0] == jwslib.JWS_ERROR_SUCCESS:
            error = False
            print "Data successfuly saved to file %s" % output_fn #debug
            pass
        elif wresults[0] == jwslib.JWS_ERROR_COULD_NOT_CREATE_FILE:
            print "Could not create/open file '%s'" % output_fn #debug
            pass
        else:
            print "Unknown error saving to file %s" % output_fn #debug
            pass
        if not error:
            saved_counter += 1
    print "Saved %d of %d sucessfully processed files." \
            % (saved_counter, len(processed_files)) #debug
    return saved_counter


class JwsProcessor:
    def __init__(self, progress_window):
        self.base_label_text = _("Processing file %(#)d of %(##)d...")
        self.loop_running = False
        self.progress_window = progress_window
        self.report_buffer = gtk.TextBuffer()
        self.report_buffer.create_tag("redtag", foreground="red")

    def info(self, text):
        self.report_buffer.insert_at_cursor(text)

    def error(self, text):
        self.report_buffer.insert_with_tags_by_name(self.report_buffer.get_end_iter(),
                                                    text,
                                                    "redtag")
    def start_loop(self):
        self.loop_running = True
        self.progress_window.start_loop()
        # informar a progres_window
        
    def abort_loop(self, text):
        self.error(text)
        self.progress_window.finish_loop()


    def finish_loop(self, text):
        self.info(text)
        self.progress_window.finish_loop()

    def progress(self, counter, total):
        self.progress_window.update_progress(progress=float(counter)/float(total),
                                             title=self.base_label_text % {'#':counter, '##':total})
    
    def process_files(self, spectra_list, options):
        ''' Returns None if blank could not be loaded
            Returns a tupple (process_dict, success_count)
              * process_dict: a dictionary with processed files and the results
                of the processing:
                    process_dict[filename] = (jws_header, channel_data_list)
                or
                    process_dict[filename] = None
                    (if filename couldn't be processed)                    
              * success_count: number of the files successfully processed
              * report_failed: if False, process_dict will contain only files
                sucessfully processed, i.e. all process_dict entries will have
                as value a tuple (jws_header, cannel_data_list)
        '''
        self.start_loop()
        if options.subtract_blank:
            self.info(_("\n**Loading blank file: %s**\n") % options.blank_fn)
            results = self.load_blank(options.blank_fn)
            if results:
                (blank_header, blank_channels) = results
            else:
                self.abort_loop(_("Blank could not be loaded"))
                return None
        else:
            blank_header = None
            blank_channels = None
        
        processed_files = {}
        processed_list = []        
        total = len(spectra_list)
        counter = 0
        success_count = 0
        for input_fn, dilution_factor in spectra_list:
            counter += 1
            self.progress(counter, total)
            self.info(_("\n**Processing %s**\n") % input_fn)
            # process_file() returns a tuple (header, channels) or None if failed
            results = self.process_file(input_fn, dilution_factor, blank_header, blank_channels, options) 
            if results:
                processed_files[input_fn] = results
                processed_list.append(input_fn)
                success_count += 1

        self.finish_loop(_("\nSuccessfully processed %(#)d of %(#)d files\n") % \
                         {'#':success_count, '##':total})
        return (processed_files, processed_list, success_count)

    def process_file(self, input_fn, dilution_factor, blank_header, blank_channels, options):
        # Read input file
        error = True
        results = jwslib.read_file(input_fn)
        if results[0] == jwslib.JWS_ERROR_SUCCESS:                                    
            error = False
        elif results[0] == jwslib.JWS_ERROR_COULD_NOT_READ_FILE:
            self.error(_("Error reading jws file %(#)s:\n%(##)s\n") % {'#':input_fn, '##':results[1]} )
        elif results[0] == jwslib.JWS_ERROR_INVALID_FILE:
            self.error(_("Invalid file %(#)s:\n%(##)s\n") % {'#':input_fn, '##':results[1]})
        else:
            self.error(_("Unknown error loading %s\n") % input_fn)
        if error:
            return None

        header = results[1]
        channels = results[2]
        n_channels = len(channels)

        # Print information about the file
        self.print_header_info(header, input_fn)
        self.info(_("Read data for %d channels\n") % n_channels)
        # Exit if we don't have channel data to process
        if n_channels < 1:
            self.error(_("Error: This file has no channel data\n"))
            return None
        ellipticity = array(channels[0], float32)

        # Subtract blank
        if options.subtract_blank:
            error = True
            if blank_header.point_number < header.point_number:
                self.error(_("Error: Blank has not enough data to be subtracted to input.\n"))
            elif blank_header.x_for_first_point != header.x_for_first_point:
                self.error(_("Error: Blank has no data in the wavelength range of input.\n"))
            else:
                error = False
            if error: 
                return None
            blank = array(blank_channels[0][:len(channels[0])], float32)
            subtract(ellipticity, blank, ellipticity)

        # Make ellipticity at 260nm 0
        if options.subtract260 and options.subtract_blank:
            if header.x_for_first_point == 260.0:
                self.info(_("Making ellipticity at 260nm 0...\n"))
                subtract(ellipticity, ellipticity[0], ellipticity)

        # Apply smoothing
        if options.smoothing:
            self.info(_("Applying smoothing...\n"))
            m = options.get_clamped_m()
            if options.smoothing_type == "mm":
                ellipticity = pysmoothing.mean_movement(ellipticity, m)
            elif options.smoothing_type == "sg":
                p = options.get_clamped_p()
                ellipticity = pysmoothing.sgolayfilt(ellipticity, p, m)
            ellipticity = array(ellipticity, float32)
            
        # Apply correction factor:
        if options.correct:
            multiply(ellipticity, options.correction_factor, ellipticity)

        if options.correct_dilution:
            multiply(ellipticity, dilution_factor, ellipticity)
            
        channels[0] = list(ellipticity)
        return (header, channels)

    def load_blank(self, blank_fn):        
        results = jwslib.read_file(blank_fn)
        error = True
        if results[0] == jwslib.JWS_ERROR_SUCCESS:
            blank_header = results[1]                
            blank_channels = results[2]
            if len(blank_channels) < 1:
                self.error(_("Error: Blank has no channel data.\n"))
            else:
                error = False
        elif results[0] == jwslib.JWS_ERROR_COULD_NOT_READ_FILE:
            self.error( _("Error reading blank file %(#)s:\n%(##)s\n") % \
                        {'#':blank_fn, '##':results[1] } )

        elif results[0] == jwslib.JWS_ERROR_INVALID_FILE:
            self.error(_("Invalid blank file %(#)s:\n%(##)s\n") % {'#':blank_fn, '##':results[1]})
        else:
            self.error(_("Unknown error loading blank\n"))
        if error:
            return None
        else:            
            return (blank_header, blank_channels)

    def print_header_info(self, header, fn):    
        header_info = _('''Information for file %(fn)s
 -Channels %(chans)d
 -Points: %(points)d
 -From %(fp)f to %(lp)f
 -Data pitch: %(dp)f\n''') % {'fn': fn,     
                              'chans':header.channel_number, 
                              'points':header.point_number, 
                              'fp': header.x_for_first_point, 
                              'lp':header.x_for_last_point,
                              'dp':header.x_increment }
        self.info(header_info)




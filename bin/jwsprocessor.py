#!/usr/bin/env python

import os, sys, imp
from ConfigParser import ConfigParser

debug = '--debug' in sys.argv

# This is to enable running from a repository, from a source distribution, or 
# from a binary distribution
# In repositories or in a source distribution the jwsprocessor package will be 
# in "../src". In a binary distribution, the jwsprocessor packages will be in 
# "../lib"
CWD = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if os.path.isfile(os.path.join(CWD, 'this_is_a_repository')):
    search_dirs = [ os.path.normpath(os.path.join(CWD, '../src')),      
                    os.path.normpath(os.path.join(CWD, '../lib')),
                  ]
    module_path = None
    for path in search_dirs:
        if os.path.isdir(path):
            module_path = path
            break
    if module_path is not None:
        print "adding " + module_path + " to sys.path"
        sys.path = [module_path] + sys.path
    else:
        print "Warning: path to jwsprocessor python package not found."
        print "Will try to import 'jwsprocessor' package anyway."

try:
    import jwsprocessor.main
except ImportError:
    print "'jwsprocessor' package could not be found!"
    sys.exit(-1)

jwsprocessor.main.main(debug)


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

# Add jwsprocessor installation directory to sys.path if it is not there already
# In Ubuntu 9.04 (Jaunty) Python 2.6 path only includes ${PYTHON_DIR}/dist-packages
# and custom built modules are installed in ${PYTHON_DIR}/site-packages.
# See bug: https://bugs.launchpad.net/ubuntu/+source/python2.6/+bug/362570/
# We first check where jwsprocessor module was installed (in the 
# /etc/jwsprocessor/path.cfg file) and if it is not in sys.path, add it.
def _check_site_packages():
    HOME_CONFIG_DIR = '~/.jwsprocessor'

    if 'JWSPROCESSOR_PATHCONFIG' in os.environ:
	    PATHCONFIG = os.environ['JWSPROCESSOR_PATHCONFIG']
    else:
	    PATHCONFIG = 'etc/debugpath.cfg'

    if 'JWSPROCESSOR_BASE_PATH' in os.environ:
	    BASE_PATH = os.environ['JWSPROCESSOR_BASE_PATH']
    else:
	    BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

    CFG_PATHS = [
	    PATHCONFIG, # assume we are in the repository
	    HOME_CONFIG_DIR + '/path.cfg', # is it in home dir config folder?
	    '/etc/jwsprocessor/path.cfg', # take the absolute path
    ]

    c = ConfigParser()
    CFG_PATH = None
    for path in CFG_PATHS:
	    path = os.path.expanduser(path)
	    if not os.path.isabs(path):
		    path = os.path.normpath(os.path.join(BASE_PATH,path))
	    print "searching " + path
	    if os.path.isfile(path):
		    print "using " + path
		    CFG_PATH = path
		    break
    assert CFG_PATH, "Unable to find path.cfg"
    c.read([CFG_PATH])
    if c.has_option('Paths', 'site_packages'):	    
	    value = os.path.expanduser(c.get('Paths', 'site_packages'))
	    if not os.path.isabs(value):
		    value = os.path.normpath(os.path.join(BASE_PATH, value))
	    site_packages = value
    else:
        return
    if not site_packages in sys.path:
        print site_packages + "  missing in sys.path, prepending"
        sys.path = [site_packages] + sys.path

try:
    import jwsprocessor.main
except ImportError:
    _check_site_packages()
    try:
        import jwsprocessor.main
    except ImportError:
        print "'jwsprocessor' package could not be found!"
        sys.exit(-1)

jwsprocessor.main.main(debug)


#!/usr/bin/env python
#encoding: utf-8

#
# This setup file is to create an msi installer for Windows, to install on unixes
# refer to README.
#
from distutils.core import setup
from distutils.core import Command
from distutils.file_util import copy_file

import sys, glob, os

# The msgfmt.py script comes from Python distribution.
sys.path.append("buildtools")
import msgfmt

class build_mo (Command):
    # Brief (40-50 characters) description of the command
    description = "Builds the message catalog files for internationalization."

    # List of option tuples: long name, short name (None if no short
    # name), and help string.
    user_options = [('po-dir', None,
                     "Directory where po files are kept"
                     "(default 'po'"),
                    ('locale-dir', None,
                     "Directory where the catalog will be built"
                     "Default 'share/locale'"),
                   ]

    def initialize_options (self):
        self.po_dir = None
        self.locale_dir = None

    def finalize_options (self):
        if self.po_dir is None:
            self.po_dir = 'po'
        if self.locale_dir is None:
            self.locale_dir = 'share/locale'
            
    def run (self):
        self.mkpath(self.locale_dir)                    
        for po in glob.glob(os.path.join(self.po_dir, '*.po')):
            lang = os.path.splitext(os.path.basename(po))[0]
            gmo = po.replace('.po', '.gmo') 
            msgfmt.make(po, gmo) 
            destdir = os.path.join(self.locale_dir, lang, 'LC_MESSAGES')
            destfile = os.path.join(destdir, "jwsprocessor.mo")
            self.mkpath(destdir)
            self.copy_file(gmo, destfile)
            self.distribution.data_files.append( (destdir, [destfile]))

#make sure build_mo is called when the package is built
import distutils.command.build 
distutils.command.build.build.sub_commands.append( ('build_mo', None) )

mo_catalog = []
for dirpath, dirnames, filenames in os.walk('share/locale'):
    if 'LC_MESSAGES' in dirnames:
        modir = os.path.join(dirpath,'LC_MESSAGES')
        mofile = os.path.join(modir, "jwsprocessor.mo")
        if os.path.isfile(mofile):
            mo_catalog.append( (modir, [mofile,]) )
        
        
data_files = [('pixmaps', ['pixmaps/jwsprocessor.svg', 'pixmaps/jwsprocessor.png']),
              ('etc', ['etc/debugpath.cfg']),
              ('doc', ['README', 'AUTHORS', 'LICENSE', 'ChangeLog']), 
              ('bin', ['bin/jwsprocessor.py', 'bin/this_is_a_repository']),
             ]

data_files.extend(mo_catalog)

    
setup(cmdclass={'build_mo':build_mo},
      name='jwsConverter',
      version='0.1',
      description='A program to convert and process Jasco SpectraManager (JWS) files.',
      author='Victor M. Hernandez-Rocamora',
      author_email='victor.hr@gmail.com',
      url='http://victor_hr.googlepages.com',
      package_dir = { 'jwsprocessor': 'src/jwsprocessor' },
      packages=['jwsprocessor'],
      data_files = data_files
     )


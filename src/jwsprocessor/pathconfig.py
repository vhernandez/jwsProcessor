#encoding: utf-8

# jwsProcesor
# A program to convert and process Jasco SpectraManager files (JWS) files.
# Copyright (C) 2007-2009 Víctor M. Hernández-Rocamora
#
# Adapted from Aldrin:
#
# Aldrin
# Modular Sequencer
# Copyright (C) 2006,2007,2008 The Aldrin Development Team
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
Organizes finding jwsProcessor resources across the system.
"""

from ConfigParser import ConfigParser
import sys, os

HOME_CONFIG_DIR = '~/.jwsprocessor'

if 'JWSPROCESSOR_PATHCONFIG' in os.environ:
	PATHCONFIG = os.environ['JWSPROCESSOR_PATHCONFIG']
else:
	PATHCONFIG = 'etc/debugpath.cfg'

if 'JWSPROCESSOR_BASE_PATH' in os.environ:
	BASE_PATH = os.environ['JWSPROCESSOR_BASE_PATH']
else:
	BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

class PathConfig(ConfigParser):
	CFG_PATHS = [
		PATHCONFIG, # assume we are in the repository
		HOME_CONFIG_DIR + '/path.cfg', # is it in home dir config folder?
		'/etc/jwsprocessor/path.cfg', # take the absolute path
	]
	
	def __init__(self):
		ConfigParser.__init__(self)
		CFG_PATH = None
		for path in self.CFG_PATHS:
			path = os.path.expanduser(path)
			if not os.path.isabs(path):
				path = os.path.normpath(os.path.join(BASE_PATH,path))
			print "searching " + path
			if os.path.isfile(path):
				print "using " + path
				CFG_PATH = path
				break
		assert CFG_PATH, "Unable to find path.cfg"
		self.read([CFG_PATH])
		site_packages = self.get_path('site_packages')
		if not site_packages in sys.path:
			print site_packages + "  missing in sys.path, prepending"
			sys.path = [site_packages] + sys.path
			
	def get_paths(self, pathid, append=''):
		paths = []
		default_path = self.get_path(pathid, append)
		if default_path:
			paths.append(default_path)
		paths.append(os.path.expanduser(os.path.join(HOME_CONFIG_DIR, pathid)))
		return paths
		
	def get_path(self, pathid, append=''):
		if not self.has_option('Paths', pathid):
			return None
		value = os.path.expanduser(self.get('Paths', pathid))
		if not os.path.isabs(value):
			value = os.path.normpath(os.path.join(BASE_PATH, value))
		if append:
			value = os.path.join(value, append)
		return value

path_cfg = PathConfig()


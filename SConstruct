#encoding: utf-8

# jwsProcesor
# A program to convert and process Jasco SpectraManager (JWS) files.
# Copyright (C) 2007-2009 Víctor M. Hernández-Rocamora
#
# adapted from Aldrin's scons scripts:
#
# Aldrin
# Modular Sequencer
# Copyright (C) 2006 The Aldrin Development Team

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
#

def read_version():
    f = file("VERSION", "r")
    v = f.read()
    f.close()
    return v.strip()

VERSION = read_version()

import os, glob, sys, time
import distutils.sysconfig

posix = os.name == 'posix'
win32 = os.name == 'nt'
mac = os.name == 'mac'

######################################
#
# init environment and define options
#
######################################

def tools_converter(value):
	return value.split(',')
	
def bool_converter(value):
	if value == 'True':
		return True
	elif value == 'False':
		return False
	return bool(value)

opts = Options( 'options.conf', ARGUMENTS )
opts.Add("PREFIX", 'Set the install "prefix" ( /path/to/PREFIX )', "/usr/local")
opts.Add("DESTDIR", 'Set the root directory to install into ( /path/to/DESTDIR )', "")
opts.Add("ETCDIR", 'Set the configuration dir "prefix" ( /path/to/ETC )', "/etc")

env = Environment(ENV = os.environ, options=opts, tools=['default','packaging'])

env.SConsignFile()

######################################
# build settings
######################################

env['ROOTPATH'] = os.getcwd()
env['SITE_PACKAGE_PATH'] = distutils.sysconfig.get_python_lib(prefix="${DESTDIR}${PREFIX}")
env['APPLICATIONS_PATH'] = '${DESTDIR}${PREFIX}/share/applications'
env['BIN_PATH'] = '${DESTDIR}${PREFIX}/bin'
env['SHARE_PATH'] = '${DESTDIR}${PREFIX}/share/jwsprocessor'
env['DOC_PATH'] = '${DESTDIR}${PREFIX}/share/doc/jwsprocessor'
env['ETC_PATH'] = '${DESTDIR}${ETCDIR}/jwsprocessor'
env['PIXMAPS_PATH'] = '${DESTDIR}${PREFIX}/share/pixmaps'
env['LOCALE_PATH'] = '${DESTDIR}${PREFIX}/share/locale'


CONFIG_PATHS = dict(
	site_packages = 'SITE_PACKAGE_PATH',
	applications = 'APPLICATIONS_PATH',
	bin = 'BIN_PATH',
	share = 'SHARE_PATH',
	doc = 'DOC_PATH',
	pixmaps = 'PIXMAPS_PATH',
    etc = 'ETC_PATH',
    locale = 'LOCALE_PATH',
)

env['GETTEXT_PACKAGE'] = 'jwsprocessor'

######################################
# save config
######################################

opts.Save('options.conf', env)
Help( opts.GenerateHelpText( env ) )

######################################
# install paths
######################################

try:
	umask = os.umask(022)
	#print 'setting umask to 022 (was 0%o)' % umask
except OSError:     # ignore on systems that don't support umask
	pass

import SCons
from SCons.Script.SConscript import SConsEnvironment
SConsEnvironment.Chmod = SCons.Action.ActionFactory(os.chmod,
		lambda dest, mode: 'Chmod: "%s" with 0%o' % (dest, mode))

def InstallPerm(env, dir, source, perm):
	obj = env.Install(dir, source)
	for i in obj:
		env.AddPostAction(i, env.Chmod(str(i), perm))
	return dir

SConsEnvironment.InstallPerm = InstallPerm

def install(target, source, perm=None):
	if not perm:
		env.Install(dir=env.Dir(target), source=source)
	else:
		env.InstallPerm(dir=env.Dir(target), source=source, perm=perm)

env.Alias(target='install', source="${DESTDIR}${PREFIX}")
env.Alias(target='install', source="${DESTDIR}${ETCDIR}")

def install_recursive(target, path, mask):
	for f in glob.glob(os.path.join(path, mask)):
		install(target, f)
	for filename in os.listdir(path):
		fullpath = os.path.join(path, filename)
		if os.path.isdir(fullpath):
			install_recursive(os.path.join(target,filename), fullpath, mask)

def build_path_config(target, source, env):
	outpath = str(target[0])
	from StringIO import StringIO
	from ConfigParser import ConfigParser
	s = StringIO()
	cfg = ConfigParser()
	cfg.add_section('Paths')
	remove_prefix = '${DESTDIR}'
	for key, value in CONFIG_PATHS.iteritems():
		value = env[value]
		if value.startswith(remove_prefix):
			value = value[len(remove_prefix):]
		cfg.set('Paths', key, os.path.abspath(str(env.Dir(value))))
	cfg.write(s)
	file(outpath, 'w').write(s.getvalue())

# Using this script we don't depend on gettext being installed to build
# the compiled .mo files.
# The msgfmt.py script comes from Python distribution.
sys.path.append("buildtools")
import msgfmt

def buildinstall_po( source, env):
    po = str(source)
    lang = os.path.splitext(os.path.basename(po))[0]
    #gmo = env.Command(po.replace('.po', '.gmo'), po,
    #               	 "msgfmt -o $TARGET $SOURCE")
    gmo = po.replace('.po', '.gmo') 
    print gmo
    msgfmt.make(po, gmo)

    
    modir = os.path.join('${LOCALE_PATH}', lang, "LC_MESSAGES")
    moname = '${GETTEXT_PACKAGE}' + ".mo"
    env.InstallAs(os.path.join(modir, moname), gmo)

builders = dict(
	BuildPathConfig = Builder(action = build_path_config),  
)

env['BUILDERS'].update(builders)

Export(
	'env', 
	'install',
	'install_recursive',
    'buildinstall_po',
	'win32', 'mac', 'posix',
)

# Install documentation
for filename in ['README', 'AUTHORS', 'LICENSE', 'ChangeLog']:
	install("${DOC_PATH}", filename, 0644)

env.SConscript('applications/SConscript')
env.SConscript('bin/SConscript')
#env.SConscript('doc/SConscript')
env.SConscript('etc/SConscript')
#env.SConscript('icons/SConscript')
env.SConscript('pixmaps/SConscript')
env.SConscript('po/SConscript')
env.SConscript('src/SConscript')


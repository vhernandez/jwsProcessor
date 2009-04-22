#!/usr/bin/env python
# -*- coding: UTF8 -*-
"""
Este módulo contiene:
    * Definición de las opciones por defecto como constantes globales
    * Inicialización de la variable global config, que contiene un objeto
        ConfigParser y que guardará las opciones del programa.
    * Funciones para cargar las opciones de archivos de configuración    
"""
import sys, os
import string
import ConfigParser

### Default configuration values
##################################################
LAST_DIR_STR = 'last_dir'
DEF_GNRL_CFG = {'last_dir':(os.getcwd(),'str'), }
### Default configfile filename
PROTEIN_DB_FN = 'protein_db.db'
CFGFILE_NAME = 'jwsprocess.ini'
CFGFILE_DIR = '.jwsprocess'
CFGFILE_SECTION = 'general'
###################################################
global config
config = ConfigParser.ConfigParser()
profile_dir = os.path.expanduser('~/'+CFGFILE_DIR)

def _readSettings():
    """
    Busca el archivo de configuración del programa en las carpetas de la
    lista srchPaths. Si lo encuentra lo carga en 'config'.
    DEVUELVE: El nombre del archivo que ha cargado
    """
    
    srchPaths=[os.path.expanduser( '~/'+CFGFILE_DIR),
                                   os.path.expanduser('~'),
                                   '.']
    cfgFile = 'None'
    for spath in srchPaths:
        #crear el nombre del archivo deconfiguración
        confFile = spath + '/' + CFGFILE_NAME
        if (os.path.isfile(confFile)): #probar si el archivo existe
            c = open(confFile)
            try:
                config.readfp(c)
            except Exception, msg: #debug                
                print 'Error al abrir el archivo de configuración %s :' % confFile 
                print msg
                cfgFile = 'None'
            else:
                cfgFile = confFile
                profile_dir = spath
                break #if we load one configfile we break
            c.close()
    return cfgFile

def config_load():
    """
    Busca y carga las opciones de configuración usando la función
    _readSettings() en config (un objeto ConfigParser global).
    
    Comprueba que la sección CFGFILE_SECTION contiene todas
    las opciones necesarias, y si no le añade las opciones
    "por defecto"
    Luego comprueba el resto de seccions y si no contienen las
    opciones de una cuenta (servidor, puerto y nombre de usuario)
    las elimina.
    DEVUELVE: El nombre del archivo que ha cargado
    """
    cfgFile = _readSettings()
    if config.has_section(CFGFILE_SECTION):
        for option in DEF_GNRL_CFG:
            if not config.has_option(CFGFILE_SECTION, option):
                config.set(CFGFILE_SECTION, option, DEF_GNRL_CFG[option])
    return cfgFile


def check_option_type(option):
    """
    Esta función comprueba que una opción cargada sea del tipo
    apropiado, especificadon el el diccionario DEF_GNRL_CFG.
    Devuelve True si apropiada y False si no.
    De momento, sólo chequea si la opción es de tipo numérica o bool.
    """
    value = config.get(CFGFILE_SECTION, option)
    res = True
    if DEF_GNRL_CFG[option][1] == 'num':
        try:
            config.getint(CFGFILE_SECTION, LESS_THAN_STR)
        except: res = False
    elif DEF_GNRL_CFG[option][1] == 'bool':
        try:
            config.getboolean(CFGFILE_SECTION, option)
        except: res = False
    return res
    

def config_load_validate():
    """
    Hace lo mismo que config load, pero valida cada opción de las prefencias
    generales. Si no es del tipo correcto, carga la opción por defecto.
    """
    cfgFile = _readSettings()
    # Comporbar las opciones opciones generales:
    if config.has_section(CFGFILE_SECTION):
        for option in DEF_GNRL_CFG:
            if not config.has_option(CFGFILE_SECTION, option):
                config.set(CFGFILE_SECTION, option, DEF_GNRL_CFG[option][0])
            else:
                if not check_option_type(option):
                    config.set(CFGFILE_SECTION, option, DEF_GNRL_CFG[option][0])
    else: # si no hay sección de opciones generales, crear una nueva:
        config.add_section(CFGFILE_SECTION)
        for option in DEF_GNRL_CFG:
            config.set(CFGFILE_SECTION, option, DEF_GNRL_CFG[option][0])
    return cfgFile


def config_save(cfgFile):
    """
    Guarda la configuración. Si no existe un archivo de configuración 
    previo se guarda por defecto como ~/CFGFILE_DIR/CFGFILE_NAME
    DEVUELVE: False sin no consigue guardar la configuración
              True si sí lo consigue
    """
    if os.path.isfile(cfgFile):
        c = open(cfgFile, 'w')
        try:
            config.write(c)
        except Exception, msg:
            ###DEBUG
            print 'Error al guardar el archivo de configuración %s :' % cfgFile
            print msg 
            return False
        c.close()
    else:
        confFN = os.path.expanduser('~/'+CFGFILE_DIR+'/'+CFGFILE_NAME)
        confDIR = os.path.expanduser('~/'+CFGFILE_DIR)
        if not os.path.exists(confDIR):
            os.mkdir(confDIR)
        c = open(confFN,'w')
        try:
            config.write(c)
        except Exception, msg:
            ###DEBUG
            print 'Error al guardar el archivo de configuración %s :' % confFN
            print msg 
            return False
        else:
            cfgFile = confFN
        c.close()
    return True

def printConfigParser(): ##debug function
    for section in config.sections():
        print '[',section,']'
        for option in config.options(section):
            print '  ',option,' = ', config.get(section,option)

def imagepath(path):
	"""
	Translates a path relative to the image directory into an absolute
	path.
	
	@param path: Relative path to file.
	@type path: str
	@return: Absolute path to file.
	@rtype: str
	"""
	from pathconfig import path_cfg
	return path_cfg.get_path('pixmaps', path)

def localepath():
    """
    Returns the path to the locale directory.
    """
    from pathconfig import path_cfg
    return path_cfg.get_path('locale')


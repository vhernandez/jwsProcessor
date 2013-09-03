import OleFileIO_PL as ofio
import StringIO
from struct import unpack, calcsize

# Assume the .JWS file is packed as little-endian (x86 processors)
# For Jasco SpectraManager 1.5 files
JWS_150_HEADER_FORMAT = "<L126sHLdddlll20xlll20x6i6i6i6i32s32s64s128s32s96s148s32s16s32s32s64sl148x80s596x"
JWS_MAGIC_BYTES = 0x20537E4C

# For new OLE file format
OLE_MAGIC_BYTES = 0xE011CFD0
DATAINFO_FMT = '<LLLLLLdddLLLLdddd'
# [0,1,2,3,4] = 3, 1, 0, 1, 1
# [5] --> number of points (unsigned long)
# [6] --> x_for_first_point (double)
# [7] --> x_for_last_point (double)
# [8] --> increment (double)
# [9,11] --> 0x03010010
# [10,12] --> 0x00000000
# [11] ..> xmin
# [12] ..> ymin
# [13] ..> xmax
# [14] ..> ymax


# Error codes 
JWS_ERROR_SUCCESS = 0
JWS_ERROR_COULD_NOT_CREATE_FILE = -1
JWS_ERROR_COULD_NOT_OPEN_FILE = -2
JWS_ERROR_COULD_NOT_READ_FILE = -3
JWS_ERROR_INVALID_FILE = -4
JWS_ERROR_ERROR_WRITING_FILE = -5

# Other globals:
JWS_Z260_CUTOFF = 0.05

# Custom Exceptions
class _NotEnoughDataError(Exception):
    "Raised when not enough data is present in the .JWS file header."
    pass
    
class _WrongFileTypeError(Exception):
    "Raised when initial 4-bytes does not match the correct values for a .JWS file."
    pass

class _WrongDataError(Exception):
    "Raised when wrong data values are present in the .JWS file header."
    pass

# Classes 
class JwsHeader:
    def __init__(self, channel_number, point_number, 
                 x_for_first_point, x_for_last_point, x_increment,
                 data_size=None):
        self.channel_number = channel_number
        self.point_number = point_number
        self.x_for_first_point = x_for_first_point
        self.x_for_last_point = x_for_last_point
        self.x_increment = x_increment
        #only defined if this is the header of a v1.5 jws file
        self.data_size = data_size
       
        
def _unpack_150_jws_header(header_data):    
    if len(header_data) < 0x740:
        raise _NotEnoughDataError, "Ivalid data length!"

    data_tuple = unpack(JWS_150_HEADER_FORMAT, header_data)
    if data_tuple[0] != JWS_MAGIC_BYTES:
        raise _WrongFileTypeError, "This is not a .JWS file, four magic bytes are not valid."

    # Check if header data is correct:        
    channel_number = data_tuple[2]
    point_number = data_tuple[3]
    data_size = data_tuple[12]
    predicted_data_size = channel_number*point_number*4
    if data_size != predicted_data_size:
        raise _WrongDataError, "Predicted channel data length does not match with stored value."

    # Fill rest of the header records
    x_for_first_point = data_tuple[4]
    x_for_last_point = data_tuple[5]
    x_increment = data_tuple[6]

    return JwsHeader(channel_number, point_number, 
                     x_for_first_point, x_for_last_point, x_increment, data_size)

def _unpack_ole_jws_header(data):
    if len(data) < 96:
        raise _NotEnoughDataError, "DataInfo should be at least 96 bytes!"
    data_tuple = unpack(DATAINFO_FMT, data)
    # I have only found spectra files with 1 channel
    # So we will only support 1 channel per file, at the moment
    return JwsHeader(1, data_tuple[5], 
                     data_tuple[6], data_tuple[7], data_tuple[8])


def _read_150_header(f):
    ''' Open file and read its header (first 0x740 bytes). 
        Returns a JwsHeader object if the file is a valid JWS file v1.50.
        Returns None if the couldn't open the file, of it is not a valid JWS.
    '''
    try:
        f.seek(0)
        header_data = f.read(0x740)
        f.close()
    except IOError as msg:        
        return None, msg
    try:
        header_obj = _unpack_150_jws_header(header_data)
    except (_WrongFileTypeError, _NotEnoughDataError, _WrongDataError) as msg:        
        return None, msg
    return header_obj, None
    
def _read_ole_header(f):
    try:
        f.seek(0)
        oleobj = ofio.OleFileIO(f)
    except IOError as msg:        
        return None, msg
    if oleobj.exists('DataInfo'):
        try:
            str = oleobj.openstream('DataInfo')
            header_data = str.read()
            f.close()
        except IOError as msg:            
            return None, msg
    else:
        return None, "Invalid JWS OLE file."        
    try:
        header_obj = _unpack_ole_jws_header(header_data)
    except _NotEnoughDataError as msg:        
        return None, msg
    return header_obj, None

def read_header(fn):
    ''' Open file and read its header: first 0x740 bytes in v1.50 file format or the DataInfo 
        directory entry in an OLE file format.
        Returns a JwsHeader object if the file is a recognized format.
        Returns None if the couldn't open the file, of it is not a recognized format.
    '''
    try:
        f = open(fn, 'rb')
        data = f.read(4)
    except Exception, msg:
        print "jwslib.read_header():", msg
        return None
        
    if len(data) < 4:
        f.close()
        print "jwslib.read_header(): Invalid file, file too small."                
        return None
        
    if data[:4] =="\x4C\x7E\x53\x20":
        header_obj, err_msg = _read_150_header(f)
    elif data[:4] =="\xD0\xCF\x11\xE0":
        header_obj, err_msg = _read_ole_header(f)
    else:
        print "jwslib.read_header(): Not a recognized file format!"
        return None
        
    if not header_obj:
        print "jwslib.read_header():", err_msg
    return header_obj

def _read_ole_file(data):
    print "_read_ole_file() called"
    f = StringIO.StringIO(data)
    try:
        doc = ofio.OleFileIO(f)
    except IOError as msg:
        print "_read_ole_file():", msg
        return (JWS_ERROR_INVALID_FILE, msg)

    if doc.exists('DataInfo'):
        try:
            str = doc.openstream('DataInfo')
            header_data = str.read()
        except IOError as msg:            
            print "_read_ole_file():", msg
            return (JWS_ERROR_INVALID_FILE, msg)
    else:
        print "_read_ole_file(): no DataInfo section"
        return (JWS_ERROR_INVALID_FILE, "Invalid JWS OLE file.")
    try:
        header_obj = _unpack_ole_jws_header(header_data)
    except IOError as msg:
        print "_read_ole_file():", msg
        return (JWS_ERROR_INVALID_FILE, msg)
        
    print "_read_ole_file(): header read successfully"
    
    if doc.exists('Y-Data'):
        try:
            str = doc.openstream('Y-Data')
            ydata = str.read()
        except IOError as msg:
            return (JWS_ERROR_INVALID_FILE, "Could not read Y-Data.")
     
        if len(ydata) != header_obj.point_number*4:
            return (JWS_ERROR_INVALID_FILE, "Wrong Y-Data length.")
        
        fmt = 'f'*header_obj.point_number
        values = unpack(fmt, ydata)
        channels = [values,]
        return (JWS_ERROR_SUCCESS, header_obj, channels)
    else:
        return (JWS_ERROR_INVALID_FILE, "The file does not contain Y-Data.")


def _read_150_file(data):
    # Check file length:
    if len(data) < 0x740:
        return (JWS_ERROR_INVALID_FILE, "Invalid file, file too small.")
    # Read and check header:
    header_data = data[:0x740]
    try:
        header = _unpack_150_jws_header(header_data)
    except (_WrongFileTypeError, _NotEnoughDataError, _WrongDataError) as msg:        
        return (JWS_ERROR_INVALID_FILE,msg)
    # Read channel data:    
    channel_data = data[0x740:]
    if channel_data < header.data_size:
        return (JWS_ERROR_SUCCESS, header, [])
    channels = []
    format = "f"*header.point_number    
    for i in range(header.channel_number):
        _d = unpack(format, channel_data[(i*header.point_number*4):((i+1)*header.point_number*4)])
        if len(_d) == header.point_number:
            channels.append(_d)
        else:            
            break;
    return (JWS_ERROR_SUCCESS, header, channels)


def read_file(fn):
    ''' Load data form a .JWS file, whose filename is provided.
        This function always returns a tuple with one to three items:
            1. An integer which tells if the function suceed.
               If this value is JWS_ERROR_SUCCESS, the next who items are:
               2. A JwsHeader150 object
               3. A list, each element will be a tuple of floats (the channel
                  data). The list will have as many elements as channels are
                  read. If no channel data is read, the list will be void.
               If the value is another error, the next value will be an error
               message, explaining what failed.
    '''
    # Read file:
    try:
        # In Windows the 'b'(binary) flag is necessary !!
        f = file(fn, 'rb')
        data = f.read()
        f.close()
    except IOError as msg:
        return (JWS_ERROR_COULD_NOT_READ_FILE, msg)
        
    if len(data) < 4:
        return (JWS_ERROR_INVALID_FILE, "Invalid file, file too small.")
    
    if data[:4] =="\x4C\x7E\x53\x20":
        ret_val = _read_150_file(data)
    elif data[:4] =="\xD0\xCF\x11\xE0":
        ret_val = _read_ole_file(data)
    else:
        ret_val = (JWS_ERROR_INVALID_FILE, "Invalid file, unrecognized file format.")
    return ret_val


def dump_channel_data(fn, header, channels):
    ''' 
    Write data in channels, which must be a sequence of float-sequences, i.e.:
    [[1.0, 2.0, 3.0 ...], [1.0, 2.0 ...] ...] 
    To 'fn' argument. head must be a jwslib.JwsHeader object, which will be
    used to tell the X values.
    '''
    if len(channels) < 1:
        raise Exception, "jwslib.dump_channel_data(): 'channels' argument is a void list!"
    # Open the file to read
    try:
        f = open(fn, "w")
    except IOError as msg:
        return (JWS_ERROR_COULD_NOT_CREATE_FILE, msg)
    # Write channel data to 
    x = header.x_for_first_point
    for i in xrange(header.point_number):
        f.write("%Lg" % x)
        for j in xrange(len(channels)):
            f.write("\t%g" % channels[j][i])
        f.write("\n")
        x += header.x_increment
    f.close()
    return (JWS_ERROR_SUCCESS,)
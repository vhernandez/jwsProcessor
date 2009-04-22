from struct import unpack, calcsize

# Assume the .JWS file is packed as little-endian (x86 processors)
JWS_150_HEADER_FORMAT = "<L126sHLdddlll20xlll20x6i6i6i6i32s32s64s128s32s96s148s32s16s32s32s64sl148x80s596x"
JWS_MAGIC_BYTES = 0x20537E4C

# Error codes 
JWS_ERROR_SUCCESS = 0
JWS_ERROR_COULD_NOT_CREATE_FILE = -1
JWS_ERROR_COULD_NOT_OPEN_FILE = -2
JWS_ERROR_COULD_NOT_READ_FILE = -3
JWS_ERROR_INVALID_FILE = -4
JWS_ERROR_ERROR_WRITING_FILE = -5

# Other globals:
JWS_Z260_CUTOFF = 0.05

class JwsChannelInfo:
    def __init__(self, a, b, c, d, e, f):
        self.channel_type = a
        self.channel_int = b
        self.x_min = c
        self.y_for_x_min = d
        self.x_max = e
        self.y_for_x_max = f


class JwsHeader150_mini:
    def __init__(self, header_data):
        if len(header_data) < 0x740:
            raise Exception, "Ivalid data length!"

        data_tuple = unpack(JWS_150_HEADER_FORMAT, header_data)
        if data_tuple[0] != JWS_MAGIC_BYTES:
            raise Exception, "This is not a .JWS file, four magic bytes are not valid."

        # Check if header data is correct:        
        self.channel_number = data_tuple[2]
        self.point_number = data_tuple[3]
        self.data_size = data_tuple[12]
        self.predicted_data_size = self.channel_number*self.point_number*4
        if self.data_size != self.predicted_data_size:
            raise Exception, "Predicted channel data length does not match with stored value."

        # Fill rest of the header records
        self.x_for_first_point = data_tuple[4]
        self.x_for_last_point = data_tuple[5]
        self.x_increment = data_tuple[6]

        self.channel_info = []
        for i in range(min(self.channel_number,4)):
            ci = JwsChannelInfo(data_tuple[13+(6*i)], data_tuple[14+(6*i)],
                                data_tuple[15+(6*i)], data_tuple[16+(6*i)],
                                data_tuple[17+(6*i)], data_tuple[18+(6*i)])
            self.channel_info.append(ci)

        self.model_name = data_tuple[37]
        self.serial_no = data_tuple[38]
        self.sample_name = data_tuple[39]
        self.comment = data_tuple[40]
        self.operator = data_tuple[41]
        self.organization = data_tuple[42]

        
class JwsHeader150:
    def __init__(self, header_data):

        if len(header_data) < 0x740:
            raise Exception, "Ivalid data length!"

        # Unpack binary data in header_data with struct.unpack
        data_tuple = unpack(JWS_150_HEADER_FORMAT, header_data)

        # Check header magic bytes (first four magic bytes)
        if data_tuple[0] != JWS_MAGIC_BYTES:
            raise Exception, "This is not a .JWS file, four magic bytes are not valid."

        # Fill rest of the header records
        self.channel_number = data_tuple[2]
        self.point_number = data_tuple[3]
        self.x_for_first_point = data_tuple[4]
        self.x_for_last_point = data_tuple[5]
        self.x_increment = data_tuple[6]
        self.spectrum_type = data_tuple[7]
        self.channel1_int = data_tuple[8]
        self.channel2_int = data_tuple[9]
        self.unknown_2 = data_tuple[10]
        self.unknown_3 = data_tuple[11]
        self.data_size = data_tuple[12]
        self.channel1 = JwsChannelInfo(data_tuple[13], data_tuple[14],
                                       data_tuple[15], data_tuple[16],
                                       data_tuple[17], data_tuple[18])
        self.channel2 = JwsChannelInfo(data_tuple[19], data_tuple[20],
                                       data_tuple[21], data_tuple[22],
                                       data_tuple[23], data_tuple[24])
        self.channel3 = JwsChannelInfo(data_tuple[25], data_tuple[26],
                                       data_tuple[27], data_tuple[28],
                                       data_tuple[29], data_tuple[30])
        self.channel4 = JwsChannelInfo(data_tuple[31], data_tuple[32],
                                       data_tuple[33], data_tuple[34],
                                       data_tuple[35], data_tuple[36])
        self.model_name = data_tuple[37]
        self.serial_no = data_tuple[38]
        self.sample_name = data_tuple[39]
        self.comment = data_tuple[40]
        self.operator = data_tuple[41]
        self.organization = data_tuple[42]
        self.bandwidth = data_tuple[43]
        self.sensitivity = data_tuple[44]
        self.response = data_tuple[45]
        self.scanning_speed = data_tuple[46]
        self.monitor_wavelength = data_tuple[47]
        self.accumulation = data_tuple[48]
        self.temperature_slope = data_tuple[49]
        self.predicted_data_size = self.channel_number*self.point_number*4

        # Check if header data is correct:        
        if self.data_size != self.predicted_data_size:
            raise Exception, "Predicted channel data length does not match with stored value."

def check_jws_magic_bytes(fn):
    return_value = False
    try:
        f = open(fn, 'rb')
        first_bytes = f.read(4)
        f.close()
    except Exception, msg:
        print "jwslib.check_jws_magic_bytes():", msg
        return False
      
    if len(first_bytes) >= 4:
        if first_bytes[:4] == "\x4C\x7E\x53\x20":
            return_value = True
    return return_value
    
def read_header(fn):
    ''' Open file and read its header (first 0x740 bytes). 
        Returns a JwsHeader150 object if the file is a valid JWS file v1.50.
        Returns None if the couldn't open the file, of it is not a valid JWS.
    '''
    try:
        # In Windows the 'b'(binary) flag is necessary !!
        f = file(fn, 'rb')
        data = f.read(0x740)
        f.close()
    except Exception, msg:
        print "jwslib.read_header():", msg
        return None
        
    # Check file length:
    if len(data) < 0x740:
        print "jwslib.read_header(): Invalid file, file too small."
        return None
        
    # Read and check header:
    header_data = data[:0x740]
    try:
        header = JwsHeader150_mini(header_data)
    except Exception, msg:
        print "jwslib.read_header():", msg
        return None
    return header
    

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
    except Exception, msg:
        return (JWS_ERROR_COULD_NOT_READ_FILE, msg)
    # Check file length:
    if len(data) < 0x740:
        return (JWS_ERROR_INVALID_FILE, "Invalid file, file too small.")
    # Read and check header:
    header_data = data[:0x740]
    try:
        header = JwsHeader150_mini(header_data)
    except Exception, msg:        
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


def dump_channel_data(fn, header, channels):
    ''' 
    Write data in channels, which must be a sequence of float-sequences, i.e.:
    [[1.0, 2.0, 3.0 ...], [1.0, 2.0 ...] ...] 
    To 'fn' argument. head must be a jwslib.JwsHeader150 object, which will be
    used to tell the X values.
    '''
    if len(channels) < 1:
        raise Exception, "jwslib.dump_channel_data(): 'channels' argument is a void list!"
    # Open the file to read
    try:
        f = open(fn, "w")
    except Exception, msg:
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
    
    

import time
import datetime

BYTE_ORDER = 'little'     
BLOCK_SIZE = 32
CONTENT_START = BLOCK_SIZE+1
MAX_BUFFER = 10000
FILL_BLOCK = lambda x: x.to_bytes(BLOCK_SIZE,BYTE_ORDER)
GET_DATE = lambda:int(time.time()*10**7)
CHECK_SUM = lambda x : FILL_BLOCK(sum([int(i) for i in x]))
TIMEOUT = 5       #After X seconds we count the mesasge as lost
RETRY_LAPSE = 0.3 #each X seconds we resend unack message
CODE_SYSTEM_MSG = 0x0
CODE_USER_MSG =   0x1
CODE_PING_MSG =   0x3
CODE_PONG_MSG =   0x4

"""
Message type [1] timestamp [BLOCK_SIZE]
Content [MAX_BUFFER]
""" 

def build_packet(content,code):
    #only one byte reserved to msg type
    _c = code.to_bytes(1,BYTE_ORDER)
    _c += FILL_BLOCK(GET_DATE())
    if type(content) == bytes: _c += content
    else: _c += bytearray(str(content), 'utf-8')
    return _c, CHECK_SUM(_c)   

def get_time(packet):
    t = packet[1:BLOCK_SIZE]
    time = int.from_bytes(t,BYTE_ORDER)/10**7

def get_content(packet):
    c = packet[CONTENT_START:]
    return c.decode('utf-8')

    


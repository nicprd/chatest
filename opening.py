from socket import * 
from threading import RLock, Thread
import time
import datetime


"""
Hey Hou, 
We stablish a P2P chat 
we do it just for fun
we dont expect this to be usefull by 
any means

We have decided to maximize number of functions
We hace decided to minimize the work a function does.
"""
LOG_STR = lambda event, x="" : (f"{datetime.datetime.now()} [{event}] "+x)
if __name__ != "__main__":
    _log_f = open("logs.txt", "w+")
    LOG = lambda e,x: _log_f.write(LOG_STR(e,x))
else:
    LOG = lambda e,x: print(LOG_STR(e,x))

#byte encoding
BYTE_ORDER = 'little'     
BLOCK_SIZE = 32
MAX_BUFFER = 10000
FILL_BLOCK = lambda x: x.to_bytes(BLOCK_SIZE,BYTE_ORDER)

GET_DATE = lambda:int(time.time()*10**7)
#test checksum in BLOCK_SIZE 
CHECK_SUM = lambda x : FILL_BLOCK(sum([int(i) for i in x]))
#this codes are usefull for discerning system msg vs user msg 
CODE_SYSTEM_MSG = 0x0
CODE_USER_MSG =   0x1

"""
    Packets have this form. Not elegant nor ordered
    Lets hope it becomes nicer.
    _______________
    |1     |   32 |      ----> Message type | timestamp
    | < MAX_BUFFER|      ----> content

""" 

def build_packet(content,code):
    #only one byte reserved to msg type
    _c = code.to_bytes(1,BYTE_ORDER)
    _c += FILL_BLOCK(GET_DATE())
    if type(content) == str:
        _c += bytearray(content, 'utf-8')
    elif type(content) == int:
        _c += FILL_BLOCK(content)
    elif type(content) == bytes:
        _c += content
    return _c, CHECK_SUM(_c)   

#decorators that happen to be usefull
def DO_FOREVER(f):
    def _f(*args, **kwargs):
        while True: f(*args, **kwargs)
    return _f

def PASS_EXCEP(f):
    def _f(*args, **kwargs):
        try: 
            f(*args, **kwargs)
        except Exception as e:
            pass
    return _f

def LOG_CALL(f):
    def _f(*args, **kwargs):
        f(*args, **kwargs)
        LOG("Called", f"function {f.__name__}, with args {args}")
    return _f
        

class Channel:
    """
        Sending a message means put it in a queue { checksum : message }
        Once we receive the checksum we delete it from the queue
        Once x times we resend all the messages in the queue
        Once we receive a msg we send the checksum back

        USER_MSGS Are the chat content we received
        SYSTEM_MSGS contains only the confirmation checksum of reception

    """
    #TODO: Set buffer retrictions for sending
    #      Queue for SYSTEM_MSG
    #      Queue for send once and forget?
    #      Messages shouldnt be sent thousands of times until ack
    #      Index of attempts, take more time to send on bigger attempts num
    #                       And finally count msg as failed
    # AND LOADS OF MORE 
    
    def __init__(self, port, ip):
        self.sent_queue = {} 
        self.queue_lock = RLock()

        #checksum received only append
        self.received_chk = [] 
        #messages received append and pop
        self.received = [] #[(addr,msg)]
        
        #contains received checkhum from friend
        self.received_system = []
    
        self.addr = (ip,port,)
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind(("",port))
        self.socket.settimeout(0)
        
        #threads that do the main job
        self.main_th= Thread(target=self.main_loop)
        
        #metadata
        self.success = 0 
        self.running = False

    "adds a msg to the queue: only USER_MSG"
    @LOG_CALL
    def send(self,msg):
        _c, _sum =build_packet(msg,CODE_USER_MSG)    
        self.sent_queue[_sum] = _c
   
    "sends all msgs in queue"
    @PASS_EXCEP
    def _send(self):
        for k,v in self.sent_queue.items(): #copy is done so no need to lock?
            self.socket.sendto(v,self.addr)
     
    "Confirm reception of msg and returns checksum"    
    @LOG_CALL
    def confirm(self, msg, chk, addr):
        r, _ = build_packet(chk,CODE_SYSTEM_MSG)
        self.socket.sendto(r,addr)
    
    "Is it a new message?"
    @LOG_CALL
    def is_new_msg(self,chk):
        if chk in self.received_chk: return False
        return True 
    
    "adds the msg checking if its a new one"
    @LOG_CALL
    def add_new_msg(self, msg, chk, addr):
        self.received_chk.append(chk)
        self.received.append((addr,msg))
    
    "receives msgs and handle them" 
    @PASS_EXCEP
    def receive(self):
        msg,addr = self.socket.recvfrom(MAX_BUFFER)
        chk = CHECK_SUM(msg)
        LOG("Received msg",f"rcv {msg} from {addr}")
        if msg[0] == CODE_SYSTEM_MSG:
            content = msg[33:] 
            self.received_system.append(content)
        elif msg[0] == CODE_USER_MSG:
            self.confirm(msg,chk,addr)
            if self.is_new_msg(chk):self.add_new_msg(msg,chk,addr)
        else:
            print(f" unknown type of msg : { msg[0]}")
        return msg
    
    "removes from queue ack messages" 
    @PASS_EXCEP
    def _clean_queue(self):
        while chk:= self.received_system.pop():
            if chk in self.sent_queue.keys(): 
                del self.sent_queue[chk]
                self.success +=1
    
    def main_loop(self):
        while True:
            self._send()
            self.receive()
            self._clean_queue()
    @LOG_CALL 
    def start(self):
        self.main_th.start()
        self.running = True 

    def __repr__(self):
        return  f"""
            Channel Object binded at ({self.addr})
            Running: ({self.running})
            -Unconfirmed messages: ({len(self.sent_queue)})
            -Sent messages: ({self.success})
            """
           

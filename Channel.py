from socket import * 
from threading import RLock, Thread
import time
import datetime
####################################
from utils import *




"""
Hey Hou, 
We stablish a P2P chat 
we do it just for fun
we dont expect this to be usefull by 
any means

We have decided to maximize number of functions
We hace decided to minimize the work a function does.
"""
#byte encoding
BYTE_ORDER = 'little'     
BLOCK_SIZE = 32
MAX_BUFFER = 10000
FILL_BLOCK = lambda x: x.to_bytes(BLOCK_SIZE,BYTE_ORDER)
CONTENT_START = BLOCK_SIZE+1

GET_DATE = lambda:int(time.time()*10**7)
#test checksum in BLOCK_SIZE 
CHECK_SUM = lambda x : FILL_BLOCK(sum([int(i) for i in x]))

TIMEOUT = 5       #After 3 seconds we count the mesasge as lost
RETRY_LAPSE = 0.3 #each 0.3 seconds we resend unack message

#this codes are usefull for discerning system msg vs user msg 
CODE_SYSTEM_MSG = 0x0
CODE_USER_MSG =   0x1
CODE_PING_MSG =   0x3
CODE_PONG_MSG =   0x4

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


class Channel:
    """
        Sending a message means put it in a queue { checksum : message }
        Once we receive the checksum we delete it from the queue
        Once x times we resend all the messages in the queue
        Once we receive a msg we send the checksum back

        USER_MSGS Are the chat content we received
        SYSTEM_MSGS contains only the confirmation checksum of reception

    """
    
    def __init__(self, port=DEFAULT_PORT):
        "····Sending Side····"
        ######################
        "Only append lists"
        #Contains list of all messages that are sent
        self.out_messages = {} #  chk: (addr,msg)
        #Contains list of all ack received 
        self.ack_messages = {} #  chk: (time_exit, time_ack)
        #Contatins messages that have been dropped
        self.lost_messages = {} # chk: time_last_attempt
        "pop and push lists. Workspace"
        #this are the checksums of messages that should go out
        self.out_queue = {} # chk: time_last_attempt
        #this are the ack received awaiting to be processed.
        self.in_ack = [] #push and popA
        
        
        #this a lock for the out_queue 
        self.queue_lock = RLock()
        #this messages shouldnt

        "····Receiving Side····"
        "Only append"
        #messages received 
        self.received_chk = []
        "push and pop"
        #content of message received
        self.received = [] #[(addr,msg)]
        
        #online status
        self.port = port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind(("",port))
        self.socket.settimeout(0)
        
        #threads that do the main job
        self.main_th= Thread(target=self.main_loop)
        
        #metadata
        self.success = 0 
        self.running = False

    #throws exception if msg doesnt exists
    def get_exit_time(self, chk):
        return self.ack_messages[chk][0]
    def get_ack_time(self, chk):
        return self.ack_messages[chk][1]

    "builds packet and push it to queue"
    @LOG_CALL
    def send(self,msg,addr):
        _c, _sum =build_packet(msg,CODE_USER_MSG)    
        self._push_out(_sum,addr,_c) 
        return _c
    
    "push packet to queue"
    def _push_out(self,sum_, addr, content):
        _t = time.time()
        self.out_messages[sum_] = (addr,content)
        self.ack_messages[sum_] = [_t, 0]
        self.out_queue[sum_] = 0

    
    "messages for wich ack is not expected:lost"
    def _drop_message(self, chk):
        #if chk not in self.out_queue: return
        t = self.out_queue[chk]
        del self.out_queue[chk]
        self.lost_messages[chk] = t

    "send message form msg list by chk"
    def _send_message(self, chk):
        #better throw cause something is wrong
        #if chk not in self.out_messages: return
        msg = self.out_messages[chk]
        self.socket.sendto(msg[1],(msg[0],self.port))
        self.out_queue[chk] = time.time()
    
    "Actual send routine" 
    "sends all msgs in queue in RETRY_LAPSE remove those that TIMEDOUT"
    def _send(self):
        t = time.time()
        lost_m = []
        for k,v in self.out_queue.items(): #need to lock?
            #TODO: LAPSE should be bigger when retries are bigger
            if (self.get_exit_time(k) + TIMEOUT) < t: lost_m.append(k)
            elif v < (t + RETRY_LAPSE): self._send_message(k)
        for k in lost_m: self._drop_message(k)

    
    "removes from queue ack messages" 
    @PASS_EXCEP
    def _clean_queue(self):
        while chk:= self.in_ack.pop():
            if chk in self.out_queue.keys(): 
                del self.out_queue[chk]
                self.success +=1

    "Adds time of ack in ack_message, and adds chk to in_ack" 
    def ack_checksum(self, chk):
        if chk not in self.ack_messages: return
        _t = time.time()
        self.in_ack.append(chk)
        self.ack_messages[chk][1] = _t

 
   ##################################################
   #                Receiving Side                  #
   ##################################################

    "receives msgs and handle them"
    @PASS_EXCEP
    def receive(self):
        msg,addr = self.socket.recvfrom(MAX_BUFFER)
        chk = CHECK_SUM(msg)
        LOG("Received msg",f"rcv {msg} from {addr}")
        if msg[0] == CODE_SYSTEM_MSG:
            chk = msg[CONTENT_START:]
            self.ack_checksum(chk)
        elif msg[0] == CODE_USER_MSG:
            self.confirm(msg,chk,addr)
            if self.is_new_msg(chk): self.add_new_msg(msg,chk,addr)
        else:
            print(f" unknown type of msg : { msg[0]}")
        return msg
    
    def main_loop(self):
        while True:
            self._send()
            self.receive()
            self._clean_queue()
    "Confirm reception of msg"    
    @LOG_CALL
    def confirm(self, msg, chk, addr):
        #TODO shouldnt send it directly
        r, _ = build_packet(chk,CODE_SYSTEM_MSG)
        self.socket.sendto(r,addr)
    
    "adds the msg checking if its a new one"
    @LOG_CALL
    def add_new_msg(self, msg, chk, addr):
        self.received_chk.append(chk)
        self.received.append((addr,msg))

    "Is it a new message?"
    @LOG_CALL
    def is_new_msg(self,chk):
        if chk in self.received_chk: return False
        return True

    @LOG_CALL 
    def start(self):
        self.main_th.start()
        self.running = True 

    def __repr__(self):
        return  f"""
            Channel Object binded at ({self.port})
            Running: ({self.running})
            -messages awaiting confirmation: ({len(self.out_queue)})
            -Sent messages: ({self.success})
            -lost messages: ({len(self.lost_messages)})
            """
           

from socket import * 
from threading import RLock, Thread
import time
import datetime
#
from utils import *
from PacketParser import *

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
        "Only append lists"
        #Contains list of all messages that are sent
        self.out_messages  = {} #  chk: (addr,msg)
        #Contains list of all ack received 
        self.ack_messages  = {} #  chk: [time_exit, time_ack] 0:notack -1:dropped
        #Contatins messages that have been dropped
        self.drop_messages = {} # chk: time_last_attempt
        "pop and push lists. Workspace"
        #this are the checksums of messages that should go out
        self.out_queue = {} # chk: time_last_attempt
        #this are the ack received awaiting to be processed.
        "Only append"
        #messages received 
        self.received_chk = []
        "push and pop"
        #content of message received
        
        self.in_messages = {} #chk: (addr,msg) #breaks simmetry... 
        self.in_ack = {} #chk: time_entry  
        self.in_queue = [] #chk
        
        #online status
        self.port = port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind(("",port))
        self.socket.settimeout(0)
        
        #threads that do the main job
        self.main_th = Thread(target=self.main_loop)
    
    is_running = lambda self: self.main_th.is_alive()
    get_out_t = lambda self,chk: self.ack_messages[chk][0]
    get_ack_t = lambda self,chk: self.ack_messages[chk][1]
    get_out_msg = lambda self, chk: self.out_messages[chk]
    get_in_msg = lambda self, chk: self.in_messages[chk]
    get_in_t = lambda self, chk: self.in_ack[chk] 
    pop_in_msg = lambda self:self.in_queue.pop() if self.in_queue else None
    

    @LOG_CALL
    def send(self,msg,addr):
        content, chk =build_packet(msg,CODE_USER_MSG)    
        self._push_out(chk,addr,content) 
        return chk
    
    def _push_out(self,chk, addr, content):
        t = time.time()
        self.out_messages[chk] = (addr,content)
        self.ack_messages[chk] = [t, 0]
        self.out_queue[chk] = 0
    
    def _send_message(self, chk):
        msg = self.out_messages[chk]
        self.socket.sendto(msg[1],(msg[0],self.port))
        self.out_queue[chk] = time.time()

    def _drop_message(self, chk):
        t = self.out_queue[chk]
        self.drop_messages[chk] = t
        del self.out_queue[chk]
        self.out_messages[chk] = -1

    def _send_queue(self):
        t = time.time()
        drop_m = []
        for k,v in self.out_queue.items():
            if (self.get_out_t(k) + TIMEOUT) < t: drop_m.append(k)
            elif v < (t + RETRY_LAPSE): self._send_message(k)
        for k in drop_m: self._drop_message(k)
    
    def receive(self):
        try:
            msg,addr = self.socket.recvfrom(MAX_BUFFER)
        except BlockingIOError: return
        if msg[0] == CODE_SYSTEM_MSG:
            chk = msg[CONTENT_START:]
            self.ack_checksum(chk)
        elif msg[0] == CODE_USER_MSG:
            chk = CHECK_SUM(msg)
            self.confirm(msg,chk,addr)
            if self.is_new_msg(chk):
                self.add_new_msg(msg,chk,addr)
    
    @PASS_EXCEP
    def ack_checksum(self, chk):
        t = time.time()
        del self.out_queue[chk]
        self.ack_messages[chk][1] = t

    @LOG_CALL
    def add_new_msg(self, msg, chk, addr):
        t = time.time()
        self.in_messages[chk] = (addr[0],msg) #!!!! BE CAREFULL
        self.in_queue.append(chk)
        self.in_ack[chk] = t

    @LOG_CALL
    def is_new_msg(self,chk):
        if chk in self.in_messages.keys(): 
            return False
        return True
    
    def main_loop(self):
        while True:
            self._send_queue()
            self.receive()

    @LOG_CALL
    def confirm(self, msg, chk, addr):
        r, _ = build_packet(chk,CODE_SYSTEM_MSG)
        self.socket.sendto(r,addr)
    

    @LOG_CALL 
    def start(self): self.main_th.start()

    def __repr__(self):
        return f"Channel at port({self.port}), alive: ({self.is_running()})"
           

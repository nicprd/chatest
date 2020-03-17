from socket import * 
from threading import RLock, Thread
import time
import datetime

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
        
		#Contains list of all messages 
        self.out_messages  = {} #  chk: (addr,msg)
        #Contains list of all msg with time of exit and of reception 
        self.ack_messages  = {} #  chk: [time_exit, time_ack] 0:notack -1:dropped
        #Contatins messages that have been dropped
        self.drop_messages = {} # chk: time_last_attempt
		#this are the checksums of messages that should go out
        self.out_queue = {} # chk: time_last_attempt
        
        self.push_out_lock = RLock() 

        self.in_messages = {} #chk: (addr,msg) 
        self.in_ack = {} #chk: time_entry  
        self.in_queue = [] #chk
        
        #online status
        self.port = port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind(("",port))
        self.socket.settimeout(0)
        
        self.main_th = Thread(target=self.main_loop)
        self.lastException = None
    
    is_running = lambda self: self.main_th.is_alive()
    get_out_t = lambda self,chk: self.ack_messages[chk][0]
    get_ack_t = lambda self,chk: self.ack_messages[chk][1]
    get_out_msg = lambda self, chk: self.out_messages[chk]
    get_in_t = lambda self, chk: self.in_ack[chk] 
    get_in_msg = lambda self, chk: self.in_messages[chk]                        
    pop_in_msg = lambda self:self.in_queue.pop() if self.in_queue else None
    

    @LOG_CALL
    def send(self,msg,addr):
        content, chk =build_packet(msg,CODE_USER_MSG)    
        self._push_out(chk,addr,content) 
        return chk
    
    def _push_out(self,chk, addr, content):
        with self.push_out_lock:
            t = time.time()
            self.out_messages[chk] = (addr,content)
            self.ack_messages[chk] = [t, 0]
            self.out_queue[chk] = 0

    
    def _send_message(self, chk):
        msg = self.out_messages[chk]
        self.out_queue[chk] = time.time()
        try:
            self.socket.sendto(msg[1],(msg[0],self.port))
        except BlockingIOError as e:
            pass

    def _drop_message(self, chk):
        t = self.out_queue[chk]
        self.drop_messages[chk] = t
        del self.out_queue[chk]
        self.ack_messages[chk][1] = -1

    def _send_queue(self):
        with self.push_out_lock:
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
    
    @LOG_CALL
    def main_loop(self):
       try:
        while True:
            self._send_queue()
            self.receive()
       except Exception as e:
            self.lastException = e

    @LOG_CALL
    def confirm(self, msg, chk, addr):
        r, _ = build_packet(chk,CODE_SYSTEM_MSG)
        try:
            self.socket.sendto(r,addr)
        except BlockingIOError:
            pass

    @LOG_CALL 
    def start(self): self.main_th.start()

    def __repr__(self):
        return f"Channel at port({self.port}), alive: ({self.is_running()})"
           

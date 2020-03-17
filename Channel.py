from socket import socket, AF_INET, SOCK_DGRAM
from threading import RLock, Thread
import time
import datetime

from utils import *
from PacketParser import *

class Channel:
    
    def __init__(self, port=DEFAULT_PORT):
        
		#Contains list of all messages 
        self.out_contents  = {} #  chk: (addr,msg)
        #Contains list of all msg with time of exit and of reception 
        self.out_dates  = {} #  chk: [time_exit, time_ack] 0:notack -1:dropped
        #Contatins messages that have been dropped
        self.out_drops = {} # chk: time_last_attempt
		#this are the checksums of messages that should go out
        self.out_queue = {} # chk: time_last_attempt
        self.out_queue_rlock = RLock() 

        self.in_contents = {} #chk: (addr,msg) 
        self.in_dates = {} #chk: time_entry  
        self.in_queue = [] #chk
        
        self.port = port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind(("",port))
        self.socket.settimeout(0)
        
        self.main_th = Thread(target=self.main_loop)
        self.lastException = None
    
    def get_out_msg(self, chk): return self.out_contents[chk]
    def get_out_t(self,chk): return self.out_dates[chk][0]
    def get_ack_t(self,chk): return self.out_dates[chk][1]
    def get_in_msg(self, chk): return self.in_contents[chk] 
    def get_in_t(self,chk): return self.in_dates[chk]                    
    def pop_in_msg(self): return self.in_queue.pop() if self.in_queue  else  None
    def push_to_queue(self,chk,t): 
        with self.out_queue_rlock: self.out_queue[chk] = t 
    def is_running(self): return self.main_th.is_alive()

    @LOG_CALL
    def send(self,msg,addr):
        content, chk =build_packet(msg,CODE_USER_MSG)    
        self._push_out(chk,addr,content) 
        return chk
    
    def _push_out(self,chk, addr, content):
        t = time.time()
        self.out_contents[chk] = (addr,content)
        self.out_dates[chk] = [t, 0]
        self.push_to_queue(chk,0)
    
    def _send_message(self, chk):
        msg = self.out_contents[chk]
        self.out_queue[chk] = time.time()
        try:
            self.socket.sendto(msg[1],(msg[0],self.port))
        except BlockingIOError: pass

    def _drop_message(self, chk):
        t = self.out_queue[chk]
        self.out_drops[chk] = t
        del self.out_queue[chk]
        self.out_dates[chk][1] = -1

    def _send_queue(self):
        t = time.time()
        drop_m = []
        with self.out_queue_rlock:
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
        self.out_dates[chk][1] = t

    @LOG_CALL
    def add_new_msg(self, msg, chk, addr):
        t = time.time()
        self.in_contents[chk] = (addr[0],msg) #!!!! BE CAREFULL
        self.in_queue.append(chk)
        self.in_dates[chk] = t

    @LOG_CALL
    def is_new_msg(self,chk):
        if chk in self.in_contents.keys(): 
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
           

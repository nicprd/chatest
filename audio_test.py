import Channel
import Router
import sys
import os
import datetime
import time
from AudioHandler import AudioHandler

DATE = lambda x: datetime.datetime.fromtimestamp(int(x)) if x > 0 else "NOT YET" if x==0 else "NEVER"

try:
    addr = sys.argv[1]
except IndexError:
    print("Error, fisrt argument must be peer ip")
    print("Like: python3.8 chatest_test.py 216.239.34.117")
    exit(-1)

def display_message(elem):
    block = "___________________\n"
    if elem[0]: block += f"[Sent] at: {DATE(elem[1][1])} arrived at: {DATE(elem[1][2])}\n"
    else: block += f"[Recv] sent at: {DATE(elem[1][1])}\n"
    block += elem[1][0]
    return block

channel = Channel.Channel()
channel.start()
router = Router.Router(channel)
audioHandler = AudioHandler()


while True:

    if not channel.is_running(): raise channel.lastException
    
    router.update_conversations()

    recv = []
    while (msg:=router.pop_out_msg(addr)): 
        recv.append(router.get_out_msg(msg))
    
    feed = sorted(recv, key=lambda x: x[2], reverse=True)
    
    for i,_,__ in feed: audioHandler.play_audio(i)
    
    os.system("clear")
 
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print(f"Updated on {DATE(time.time())} Press Enter to update or send a message")
    
    router.send(audioHandler.get_audio(),addr)
    

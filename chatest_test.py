import Channel
import Router
import sys
import os

import time

try:
    addr = sys.argv[1]
except IndexError:
    print("Error, fisrt argument must be peer ip")
    exit(-1)


def display_message(elem):
    block = "___________________\n"
    if elem[0]: block += f"[Sent] at: {elem[1][1]} arrived at: {elem[1][2]}\n"
    else: block += f"[Recv] sent at: {elem[1][1]}\n"
    block += elem[1][0]
    return block

channel = Channel.Channel()
channel.start()
router = Router.Router(channel)

while True:
    if not channel.is_running(): raise channel.lastException
    router.update_conversations()
    sent, recv = router.get_conversation(addr)
    sent = [ (True,router.get_out_msg(i)) for i in sent]
    recv = [ (False,router.get_in_msg(i)) for i in recv]
    feed = sent + recv
    feed = sorted(feed, key=lambda x: x[1][1], reverse=True)
    feed = feed[:15]
    feed.reverse()
    os.system("clear")
    for i in feed[:15]: print(display_message(i)) 
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print(f"Updated on {time.time()} Press Enter to update or send a message")
    message = input("send a message:")
    if message == "": continue
    router.send(message,addr)
    

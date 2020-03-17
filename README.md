Heyhou

Chatest is a test for a chat and a chat for a test.

UDP p2p.

Behind a NAT:
Going to the outside world requires sending a packet to the ip:port you expect to receive from that same port.

What do we do here?

See Channel.py? 

Receives a message to send towards an address.
Calculates a checksum [now its a stupid sum. TODO:md5] and creates a packet
That same channel stores {cheksum : (addr,content)}
Also stores {checksum : time_it_went_out, time_reception_was_ack} (0 is not yet, -1 taken as lost)
c
heksum is sent to a queue. 
that queue is { chk : time_last_sent }
Messages are sent each 0.3 seconds until ack or timeout.  

Easy to imaging the receiving side that is in the same socket, and implemented in the same object. REMEMBER WE ARE BEHIND NAT.

We receive a message, send ACK and store it in:

{chk : (addr,content)}

Also we store {chk: received_time} 

we store the checksum in a queue where messages are popped.


See Router.py?

Router class interacts with a channel. 

The idea is to keep a track of conversations with a same address,
receive incoming messages,
query the channel for the status of messages,
and give orders to send them.

So thats pretty much it.





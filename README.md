Heyhou

Chatest is a test for a chat and a chat for a test.

UDP p2p.

Behind a NAT:
Receiving from the outside world requires sending a packet to the ip:port you expect to receive, and from that same port.

What do we do here?

See Channel.py? 

First of all sends messages out.

Calculates a checksum (now its a stupid sum, TODO:md5) and creates a packet.  
Stores {cheksum : (addr,content)}  
Stores {checksum : time_it_went_out, time_reception_was_ack} (0 is not yet, -1 taken as lost).  
Cheksum is sent to a queue {chk : time_last_sent }
Messages are sent each 0.3 seconds until ack or timeout; then removed from the queue.  

Second of all gets messages in. (REMEMBER WE ARE BEHIND NAT)

We receive a message, send ACK and store it in: {chk : (addr,content)}  
Stores {chk: received_time}   
Push the checksum in a queue where messages are popped in demand.  

See Router.py?

Router class interacts with a channel, keeping a track of conversations with an address.

Gets new messages and stores them in the aproppiate conversation:  
{ addr : [ [sent_packet_checkhums], [received_packet_checksums]]}  
Queries the channel about the status of messages,  
Gives orders to send them.  

So thats pretty much it. 

Channel runs it own threads.  
One lock is used for now without much care.Think should be put in thread safety and minimizing lock number. It will be desirable to communicate threads by using atomic operations on share objects.

Working silly test at chatest_test.  
I have no idea about making user interfaces.




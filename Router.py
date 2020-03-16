import PacketParser 

class Router:
        
    #handles communication with the channel
    #keeping information about conversations
    
    def __init__(self, channel):
        self.channel = channel
        self.conversations = {} 
    
    get_content = lambda self, chk: self.channel.get_in_msg(chk)[1]
    get_address = lambda self, chk: self.channel.get_in_msg(chk)[0] 
    is_conver = lambda self, addr: True if addr in self.conversations.keys() else False
    
    def update_conversations(self):
        if (chk := self.channel.pop_in_msg()) == None: return 
        addr = self.get_address(chk)
        if self.is_conver(addr):
            self.conversations[addr][1].append(chk)
        else:
            self.conversations[addr] = ([],[chk])

    def send(self, content, addr):
        chk = self.channel.send(content,addr)
        if self.is_conver(addr):
            self.conversations[addr][0].append(chk)
        else:
            self.conversations[addr] = ([chk],[])
        
    def get_out_msg(self, chk):
        packet = self.channel.get_out_msg(chk)[1]
        sent_t, ack_t = self.channel.ack_messages[chk]
        return (PacketParser.get_content(packet), sent_t, ack_t)

    def get_in_msg_status(self,chk):
        packet = self.channel.get_in_msg(chk)[1]
        sent_t = PacketParser.get_time(packet)
        ack_t = self.channel.get_in_t(chk)
        return (PacketParser.get_content(packet), sent_t, ack_t)
        
       

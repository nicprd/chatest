import PacketParser 

class Router:
        
    #handles communication with the channel
    #keeping information about conversations
    
    def __init__(self, channel):
        self.channel = channel
        self.conversations = {} 
        self.conversations_pop = {}
    
    get_content = lambda self, chk: self.channel.get_in_msg(chk)[1]
    get_address = lambda self, chk: self.channel.get_in_msg(chk)[0] 
    is_conver = lambda self, addr: True if addr in self.conversations.keys() else False
    get_conversation = lambda self, addr: self.conversations[addr] if self.is_conver(addr) else [[],[]]
    
    def update_conversations(self):
        if (chk := self.channel.pop_in_msg()) == None: return False
        addr = self.get_address(chk)
        if self.is_conver(addr):
            self.conversations[addr][1].append(chk)
            self.conversations_pop[addr].append(chk)
        else:
            self.conversations[addr] = ([],[chk])
            self.conversations_pop[addr] = [chk]
        return True

    def send(self, content, addr):
        chk = self.channel.send(content,addr)
        if self.is_conver(addr):
            self.conversations[addr][0].append(chk)
        else:
            self.conversations[addr] = ([chk],[])
            self.conversations_pop[addr] = [chk]
        
    def get_out_msg(self, chk):
        packet = self.channel.get_out_msg(chk)[1]
        sent_t = self.channel.get_out_t(chk)
        ack_t = self.channel.get_ack_t(chk)
        return (PacketParser.get_content(packet), sent_t, ack_t)

    def get_in_msg(self,chk):
        packet = self.channel.get_in_msg(chk)[1]
        sent_t = PacketParser.get_time(packet)
        ack_t = self.channel.get_in_t(chk)
        return (PacketParser.get_content(packet), sent_t, ack_t)

    def pop_out_msg(self,addr):
        try:
            return self.conversations_pop[addr].pop(0)
        except Exception as e:
            return None


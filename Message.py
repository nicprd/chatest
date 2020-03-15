class Message:

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

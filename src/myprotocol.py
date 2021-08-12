encode_method = 'utf-8'


class ACTION:
    SIGN_UP = lambda : '\x01'
    SIGN_IN = lambda : '\x02'
    CHATTING_LIST = lambda: '\x03'
    CHAT = lambda: '\x04'
    SEND_MSG = lambda: '\x05'
    RECV_MSG = lambda: '\x06'
    FILE = lambda: '\x07'
class RESULT:
    SUCCESS = lambda : '\x31'
    FAIL = lambda :    '\x32'

class STANDARD:
    WIDTH = lambda : 60
    HEIGHT = lambda : 30
    MAX_MESSAGE_LEN = lambda : 500

    
    
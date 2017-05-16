import socket
import struct

class TiVo(object):

    __mapper_args__ = {'polymorphic_identity':'TiVoDevice'}

    # IR codes for direct aspect ratio control
    ASPECT_CODES = ['ASPECT_CORRECTION_ZOOM', 'ASPECT_CORRECTION_PANEL',
                    'ASPECT_CORRECTION_FULL', 'ASPECT_CORRECTION_WIDE_ZOOM']

    # IR codes to toggle closed captions
    CC_CODES = ['CC_OFF', 'CC_ON']

    # IR codes to switch video modes
    VMODE_CODES = ['VIDEO_MODE_FIXED_480i', 'VIDEO_MODE_FIXED_480p',
                   'VIDEO_MODE_FIXED_720p', 'VIDEO_MODE_FIXED_1080i',
                   'VIDEO_MODE_HYBRID', 'VIDEO_MODE_HYBRID_720p',
                   'VIDEO_MODE_HYBRID_1080i', 'VIDEO_MODE_NATIVE']

    BUTTONS = {
        'TiVo': 'TIVO',
        'Info': 'INFO',
        'LiveTv': 'LIVETV',
        'Back': 'BACK',
        'Guide': 'GUIDE',
        'Up': 'UP',
        'Left': 'LEFT',
        'Right': 'RIGHT',
        'Down': 'DOWN',
        'Select': 'SELECT',
        'ThumbsDown': 'THUMBSDOWN',
        'ThumbsUp': 'THUMBSUP',
        'ChannelUp': 'CHANNELUP',
        'ChannelDown': 'CHANNELDOWN',
        'Play': 'PLAY',
        'Reverse': 'REVERSE',
        'Pause': 'PAUSE',
        'Forward': 'FORWARD',
        'Replay': 'REPLAY',
        'Slow': 'SLOW',
        'Advance': 'ADVANCE',
        'A': 'ACTION_A',
        'B': 'ACTION_B',
        'C': 'ACTION_C',
        'D': 'ACTION_D',
        ' ': 'SPACE',
        'Clear': 'CLEAR',
        'Enter': 'ENTER',
    }
    KEYBOARD_BUTTONS = {
        '-': 'MINUS',
        '=': 'EQUALS',
        '[': 'LBRACKET',
        ']': 'RBRACKET',
        '\\': 'BACKSLASH',
        ';': 'SEMICOLON',
        "'": 'QUOTE',
        ',': 'COMMA',
        '.': 'PERIOD',
        '/': 'SLASH',
        '`': 'BACKQUOTE',
        '1': 'NUM1',
        '2': 'NUM2',
        '3': 'NUM3',
        '4': 'NUM4',
        '5': 'NUM5',
        '6': 'NUM6',
        '7': 'NUM7',
        '8': 'NUM8',
        '9': 'NUM9',
        '0': 'NUM0'
    }
    SHIFT_KEYBOARD_BUTTONS = {
        # Shift on keyboard
        '_': 'MINUS',
        '+': 'EQUALS',
        '{': 'LBRACKET',
        '}': 'RBRACKET',
        '|': 'BACKSLASH',
        ':': 'SEMICOLON',
        '"': 'QUOTE',
        '<': 'COMMA',
        '>': 'PERIOD',
        '?': 'SLASH',
        '~': 'BACKQUOTE',
        '!': 'NUM1',
        '@': 'NUM2',
        '#': 'NUM3',
        '$': 'NUM4',
        '%': 'NUM5',
        '^': 'NUM6',
        '&': 'NUM7',
        '*': 'NUM8',
        '(': 'NUM9',
        ')': 'NUM0',
    }

    def __init__(self, address, port=31339, **kwargs):
        self.address = address
        self.port = port

        self.current_captions_on = False
        self.current_aspect_ratio = 0
        self.current_video_mode = 0
        self.__connect__()

    def __connect__(self):
        """ Connect to the TiVo within five seconds or report error. """
        self.sock = socket.socket()
        self.sock.settimeout(5)
        self.sock.connect((self.address, self.port))
        self.sock.settimeout(None)

    def __disconnect__(self):
        if self.sock:
            self.sock.close()

    def __send__(self, message):
        """ The core output function, called from __irsend__(). Re-__connect__ if
            necessary (including restarting the status_update thread), __send__
            message, sleep, and check for errors.
        """
        self.sock.sendall(message.encode('utf-8'))

    def __irsend__(self, *codes):
        """ Expand a command sequence for __send__(). """
        for each in codes:
            if type(each) == list:
                self.__irsend__(*each)
            else:
                self.__send__('IRCODE %s\r' % each)

    def __kbsend__(self, *codes):
        """ Expand a KEYBOARD command sequence for __send__(). """
        for each in codes:
            self.__send__('KEYBOARD %s\r' % each)

    def closed_caption(self):
        """ Toggle closed captioning. """
        self.current_captions_on = not self.current_captions_on
        self.__irsend__(self.CC_CODES[self.current_captions_on])

    def aspect_change(self):
        """ Toggle aspect ratio mode. """
        self.__irsend__(self.ASPECT_CODES[self.current_aspect_ratio])
        self.current_aspect_ratio += 1
        if self.current_aspect_ratio == len(self.ASPECT_CODES):
            self.current_aspect_ratio = 0

    def video_mode(self):
        """ Toggle video mode. """
        self.__irsend__(self.VMODE_CODES[self.current_video_mode])
        self.current_video_mode += 1
        if self.current_video_mode == len(self.VMODE_CODES):
            self.current_video_mode = 0

    def kbd_arrows(self, text, width):
        """ Translate 'text' to a series of cursor motions for the on-screen
            keyboard. Assumes the standard A-Z layout, with 'width' number
            of columns. The cursor must be positioned on 'A' at the start,
            or Bad Things will happen. This mode is now only needed with old
            code (mostly old HME apps) that hasn't been updated to support
            direct keyboard input.
        """
        current_x, current_y = 0, 0

        for ch in text.upper():
            if 'A' <= ch <= 'Z':
                pos = ord(ch) - ord('A')
                target_y = pos / width
                target_x = pos % width
                if target_y > current_y:
                    for i in xrange(target_y - current_y):
                        self.__irsend__('DOWN')
                else:
                    for i in xrange(current_y - target_y):
                        self.__irsend__('UP')
                if target_x > current_x:
                    for i in xrange(target_x - current_x):
                        self.__irsend__('RIGHT')
                else:
                    for i in xrange(current_x - target_x):
                        self.__irsend__('LEFT')
                self.__irsend__('SELECT')
                current_y = target_y
                current_x = target_x
            elif '0' <= ch <= '9':
                self.__irsend__('NUM' + ch)
            elif ch == ' ':
                self.__irsend__('FORWARD')

    def kbd_direct(self, text):
        """ Send 'text' directly using the IRCODE command. Select this mode
            by setting 'Cols' to 0.
        """
        for ch in text.upper():
            if 'A' <= ch <= 'Z':
                self.__irsend__(ch)
            elif ch in self.KEY_CODES[self.KB]:
                self.__irsend__(self.KEY_CODES[self.KB][ch])

    def kbd_direct_new(self, text):
        """ Send 'text' directly using the KEYBOARD command (Premiere only).
            Select this mode by setting 'Cols' to 0.
        """
        for ch in text:
            if 'A' <= ch <= 'Z':
                self.__kbsend__('LSHIFT', ch)
            elif 'a' <= ch <= 'z':
                self.__kbsend__(ch.upper())
            elif ch in self.KEY_CODES[self.KB]:
                self.__kbsend__(self.KEY_CODES[self.KB][ch])
            elif ch in self.KEY_CODES[self.SKB]:
                self.__kbsend__('LSHIFT', self.KEY_CODES[self.SKB][ch])

    def __handle_key__(self, key):
        """ Look up the code or other command for a keyboard shortcut.
            Unhandled keys (mainly, tab) are passed on.
        """
        if key in self.KEY_CODES[self.B]:
            self.__irsend__(self.KEY_CODES[self.B][key])
        elif key in self.KEY_CODES[self.F]:
            eval(self.KEY_CODES[self.F][key])()
        else:
            return False
        return True

    def get_status(self):
        """ Read incoming messages from the socket in a separate thread and 
            display them.
        """
        while True:
            try:
                status = self.sock.recv(80)
            except:
                status = ''
            status = status.strip().title()
            if not status:
                self.sock.close()
                self.sock = None
                break

    def __recv_bytes__(self, sock, length):
        """ Read length bytes from the socket. """
        block = ''
        while len(block) < length:
            add = self.sock.recv(length - len(block))
            if not add:
                break
            block += add
        return block

    def __recv_packet__(self, sock):
        """ Read a packet with a length header from the socket. """
        length = struct.unpack('!I', self.__recv_bytes__(sock, 4))[0]
        return self.__recv_bytes__(sock, length)

    def __send_packet__(self, sock, packet):
        """ Write a packet to the socket with a length header. """
        self.sock.sendall(struct.pack('!I', len(packet)) + packet)

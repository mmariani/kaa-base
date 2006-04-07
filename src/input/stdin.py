import sys
import tty
import termios
import os
import atexit

import kaa
import kaa.notifier

_tc_orig_settings = None
_getch_enabled = False

_keycode_names = {
    "\x1b\x5b\x41": "up",
    "\x1b\x5b\x42": "down",
    "\x1b\x5b\x43": "right",
    "\x1b\x5b\x44": "left",

    "\x1b\x4f\x50": "F1",
    "\x1b\x4f\x51": "F2",
    "\x1b\x4f\x52": "F3",
    "\x1b\x4f\x53": "F4",
    "\x1b\x5b\x31\x35\x7e": "F5",
    "\x1b\x5b\x31\x37\x7e": "F6",
    "\x1b\x5b\x31\x38\x7e": "F7",
    "\x1b\x5b\x31\x39\x7e": "F8",
    "\x1b\x5b\x32\x30\x7e": "F9",
    "\x1b\x5b\x32\x31\x7e": "F10",
    "\x1b\x5b\x32\x33\x7e": "F11",
    "\x1b\x5b\x32\x34\x7e": "F12",

    "\x1b\x5b\x32\x7e": "ins",
    "\x1b\x5b\x33\x7e": "del",
    "\x1b\x4f\x46": "end",
    "\x1b\x4f\x48": "home",
    "\x1b\x1b": "esc",
    "\x0a": "enter",
    "\x20": "space",
    "\x7f": "backspace"
}
    
def getch():
    global _getch_enabled

    if not _getch_enabled:
        getch_enable()
        _getch_enabled = True

    buf = sys.stdin.read(1)
    while buf in ("\x1b", "\x1b\x4f", "\x1b\x5b") or \
          buf[:3] in ("\x1b\x5b\x31", "\x1b\x5b\x32", "\x1b\x5b\x33"):
        buf += sys.stdin.read(1)
        if buf[-1] == "\x7e":
            break

    #print "KEYCODE:"
    #for c in buf:
    #    print "  " +  hex(ord(c)) 
    code = buf
    #buf = ""
    if code in _keycode_names:
        return _keycode_names[code]
    elif len(code) == 1:
        return code
    else:
        return "??"


def getch_enable():
    global _tc_orig_settings
    _tc_orig_settings = termios.tcgetattr(sys.stdin.fileno())
    tc = termios.tcgetattr(sys.stdin.fileno())
    tc[3] = tc[3] & ~(termios.ICANON | termios.ECHO)
    tc[6][termios.VMIN] = 1
    tc[6][termios.VTIME] = 0
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, tc)
    atexit.register(getch_disable)
    

def getch_disable():
    global _tc_orig_settings
    if _tc_orig_settings != None:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, _tc_orig_settings)
    os.system("stty echo")


def _handle_stdin_keypress(fd):
    ch = getch()
    kaa.signals["stdin_key_press_event"].emit(ch)
    return True


_dispatcher = kaa.notifier.SocketDispatcher(_handle_stdin_keypress)

def _keypress_signal_changed(signal, flag):
    if flag == kaa.notifier.Signal.SIGNAL_CONNECTED and signal.count() == 1:
        getch_enable()
        _dispatcher.register(sys.stdin)
    elif flag == kaa.notifier.Signal.SIGNAL_DISCONNECTED and signal.count() == 0:
        getch_disable()
        _dispatcher.unregister()


# init
_signal = kaa.notifier.Signal(changed_cb = _keypress_signal_changed)
kaa.signals["stdin_key_press_event"] = _signal
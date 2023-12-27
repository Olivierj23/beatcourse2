# ------------------------------
#
# Copyright (c) 2020, Eran Egozy. All rights reserved.
# Released under GNU GPL version 3
#
# -------------------------------

from ctypes import *
from ctypes.util import find_library

from collections import namedtuple
import os
import subprocess
import numpy as np
import platform

system = platform.system()

# find correct library to load based on system
if system == 'Windows':
    lib_path, lib_file = 'leap/x64', './LeapC.dll'
elif system == 'Darwin':
    lib_path, lib_file = 'leap/osx', 'libLeapC.so'
elif system == 'Linux':
    lib_path, lib_file = 'leap/linux', './libLeapC.so'
else:
    print('Unknown system:', system)

# lib_path is actually relative to this here file (leap.py)
lib_path = os.path.join(os.path.dirname(__file__), lib_path)

# on mac, remove special attribute so that os will not complain about unsigned binaries:
if system == 'Darwin':
    bins = 'leapc_server', lib_file
    for b in bins:
        fp = os.path.join(lib_path, b)

        # get the file's attributes, and delete com.apple.quarantine if it exists
        ret = subprocess.check_output(f'xattr "{fp}"', shell=True).decode()
        if 'com.apple.quarantine' in ret:
            print(f'Removing com.apple.quarantine from "{fp}"')
            subprocess.call(f'xattr -d com.apple.quarantine "{fp}"', shell=True)

# this is done for Windows and Linux so that we can find and load the
# library: cd to the directory with the library so that sibling dlls can be loaded from the cwd.
prev_dir = os.getcwd()
os.chdir(lib_path)
_leap = CDLL(lib_file)
os.chdir(prev_dir)

# structures from the LeapC code. These must match exactly with the structures in LeapC.h


# TODO: the arm mac code requires the use of packed structs
# however, our windows and linux code was compiled before that change, and so has structs with padding
# right now we just declare _pack_ = 1 only on mac, which is a bit hacky
# ideally, we'd recompile windows and linux so that we have packed structs everywhere

class cLeapInfo(Structure):
    if system == 'Darwin':
        _pack_ = 1
    _fields_ = [
        ('service', c_bool),
        ('connected', c_bool),
        ('has_focus', c_bool),
    ]


class cLeapFinger(Structure):
    if system == 'Darwin':
        _pack_ = 1
    _fields_ = [
        ('id', c_int),
        ('pos', c_float*3),
    ]


class cLeapHand(Structure):
    if system == 'Darwin':
        _pack_ = 1
    _fields_ = [
        ('id', c_int),
        ('palm_pos', c_float*3),
        ('fingers', cLeapFinger*5),
    ]


class cLeapFrame(Structure):
    if system == 'Darwin':
        _pack_ = 1
    _fields_ = [
        ('valid', c_bool),
        ('hands', cLeapHand*2),
    ]


# set up function args
_leap.getInfo.argtypes = [POINTER(cLeapInfo)]
_leap.getFrame.argtypes = [POINTER(cLeapFrame)]


def toArray(p):
    return np.array((p[0], p[1], p[2]))


# public interface:
LeapInfo = namedtuple('LeapInfo', 'service connected has_focus')


class LeapHand(namedtuple('LeapHand', 'id palm_pos fingers')):
    def __str__(self):
        'add a custom printing for a hand so it looks nicer'
        fingers = '\n    ' + '\n    '.join([str(f) for f in self.fingers])
        return 'LeapHand(id={}, palm_pos={}, fingers=[{}])'.format(self.id, self.palm_pos, fingers)


class LeapFrame(namedtuple('LeapFrame', 'valid hands')):
    """
    Custom data structure for positional data from the Leap sensor.
    """

    def __str__(self):
        'add a custom printing for a frame so it looks nicer'
        hands = '\n  ' + '\n  '.join([str(h) for h in self.hands])
        return 'LeapFrame(valid={}, hands=[{}])'.format(self.valid, hands)


# public functions
def getLeapInfo():
    """
    Returns a structure with the following fields.

    Fields
        | **service** -  True if drivers are installed.
        | **connected** - True if the Leap is connected to the computer.
        | **has_focus** - True if the app is currently in the foreground.
    """
    info = cLeapInfo()
    _leap.getInfo(info)

    return LeapInfo(service=info.service, connected=info.connected, has_focus=info.has_focus)


def getLeapFrame():
    """
    Returns a LeapFrame containing 3D position data from the Leap
    sensor for all hands.

    Fields
        | **valid** - True if everything is working.
        | **hands** - An array of LeapHands.

    Each LeapHand contains the following fields -

    Fields
        | **id** - An positive integer identifier for the hand, -1 when no hand is detected.
            When a hand exits and re-enters the sensing area, it is assigned a new id.
        | **palm_pos** - A numpy array ``[x, y, z]`` of the palm position in millimeters.
        | **fingers** - A 5-element array of finger positions as numpy arrays ``[x, y, z]`` in millimeters.
    """

    frame = cLeapFrame()
    _leap.getFrame(frame)

    hands = [LeapHand(id=h.id,
                      palm_pos=toArray(h.palm_pos),
                      fingers=[toArray(f.pos) for f in h.fingers])
             for h in frame.hands]
    return LeapFrame(valid=frame.valid, hands=hands)


# done so that leapc on mac can find the leapc_server file
prev_dir = os.getcwd()
os.chdir(lib_path)
_leap.init()
os.chdir(prev_dir)


def run_test():
    import time

    while 1:

        info = getLeapInfo()
        frame = getLeapFrame()

        print(info)
        print(frame)

        time.sleep(.5)


# normally, this file is used as a library that you import
# however, you can also just test by running "python leap.py" to see if things are working
if __name__ == "__main__":
    run_test()

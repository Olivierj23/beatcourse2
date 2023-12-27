#
# Your final project goes here!
#

# This file just has a BaseWidget, nothing else.
# You may find ScreenManager helpful in your project.
# Check out the lecture7.py code for an example of that.

# (also, you don't have to use this code - feel free to delete this file and make a new main.py)

import sys, os
sys.path.insert(0, os.path.abspath('..'))


from imslib.audio import Audio
from imslib.core import BaseWidget, run, lookup
from imslib.gfxutil import topleft_label, resize_topleft_label, CLabelRect, CEllipse, AnimGroup, KFAnim, CRectangle
from imslib.screen import ScreenManager, Screen

from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from kivy.graphics import Color, Ellipse, PushMatrix, PopMatrix, Translate, Scale, Rotate
from kivy.uix.button import Button
from kivy import metrics
from kivy.uix.label import Label

from imslib.mixer import Mixer
from imslib.wavegen import WaveGenerator
from imslib.wavesrc import WaveBuffer, WaveFile

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle, Triangle
from kivy.core.window import Window
from kivy.uix.image import Image
import numpy as np
import pandas as pd

movement_time = 3.5 #default is 3.5

now_position = Window.width/2

"""
Helper Functions
"""
def inside(point, center, size):
    """
    helper function to determine if a point was inside a centered rectangle
    """
    x_pos = point[0]
    y_pos = point[1]

    if center[0]-size[0]/2 < x_pos < center[0] + size[0]/2\
        and center[1]-size[1]/2 < y_pos < center[1] + size[1]/2:
        return True
    else:
        return False

def beat_from_line(line):
    time, type, lane, dur = line.strip().split('\t')
    return (float(time), type, int(lane), float(dur))

"""
Helper Classes
"""

class MovingLabel(CLabelRect, InstructionGroup):
    def __init__(self, **kwargs):
        super(MovingLabel, self).__init__(**kwargs)
        self.time = 0

    def on_click(self):
        pass

    def on_update(self, dt):
        self.time += dt
        # print(self.time)

class AudioController(object):
    def __init__(self, song_folder_path, main_widget=None):
        super(AudioController, self).__init__()
        self.main_widget = main_widget
        self.audio = Audio(2)
        self.mixer = Mixer()
        self.mixer.set_gain(3)
        self.audio.set_generator(self.mixer)

        # initializes generators for the song and guitar files

        self.song = WaveGenerator(WaveFile(song_folder_path + "/song.wav"))
        self.jump = WaveGenerator(WaveFile("gameplay_sounds/jump.wav"))
        if "guitar.wav" in os.listdir(song_folder_path):
            self.guitar = WaveGenerator(WaveFile(song_folder_path + "/guitar.wav"))
            self.guitar.set_gain(0.3)
            self.mixer.add(self.guitar)
        else:
            self.guitar = None
        self.song.set_gain(0.3)
        self.jump.set_gain(0.15)
        self.mixer.add(self.song)
        self.mixer.add(self.jump)

        # start paused
        self.song.pause()
        self.jump.pause()
        if self.guitar:
            self.guitar.pause()

        self.time_since_last_miss = 0

    # start / stop the song
    def toggle(self):
        self.song.play_toggle()
        if self.guitar:
            self.guitar.play_toggle()

    # mute / unmute the solo track
    def set_mute(self, mute):
        # print(self.get_time() - self.time_since_last_miss)
        if self.get_time() - self.time_since_last_miss > 0.4:
            self.song.set_gain(mute)


    # play a sound-fx (miss sound)
    def play_miss(self):
        if self.get_time() - self.time_since_last_miss > 1:
            # self.miss.release()
            # self.miss = WaveGenerator(WaveFile("../data/Guitar-Hero-III-Missed-Note-Sound-Effects.wav"))
            # self.mixer.add(self.miss)
            # self.miss.play()
            self.time_since_last_miss = self.get_time()
        else:
            pass

    def play_jump(self):
        self.jump.release()
        self.jump = WaveGenerator(WaveFile("gameplay_sounds/jump.wav"))
        self.jump.set_gain(0.15)
        self.mixer.add(self.jump)
        self.jump.play()




    # return current time (in seconds) of song
    def get_time(self):

        return self.song.frame/self.audio.sample_rate
        #need to subtract 0.8 seconds for headphone delay

    # needed to update audio
    def on_update(self):
        # print(self.get_time() - self.time_since_last_miss)
        self.audio.on_update()

class SongData(object):
    def __init__(self, filepath):
        super(SongData, self).__init__()
        self.beats = []
        beats_file = filepath
        lines = open(beats_file).readlines()
        self.beats = [beat_from_line(l) for l in lines]


    def get_beats(self):
        return self.beats

"""
Menu Objects
"""

class SpinningObject(InstructionGroup):
    def __init__(self, position, main_widget=None):
        super(SpinningObject, self).__init__()
        self.main_widget = main_widget


        self.color = Color(1,1,1)
        self.radius = Window.width/32
        self.middle_pos = (position[0], position[1])
        self.shape = CEllipse(cpos=(position[0], position[1]), csize=(2*self.radius, 2*self.radius), segments=self.main_widget.segments)
        self.add(PushMatrix())
        self.add(self.color)
        self.rotation = Rotate(angle=0, origin=self.shape.cpos)
        self.add(self.rotation)
        self.add(self.shape)

        self.add(PopMatrix())

        self.animator = None
        self.is_jumping = False





    def on_resize(self):
        self.radius = Window.width / 32
        self.shape.cpos = (Window.width / 2, Window.height * 7 / 8)
        self.rotation.origin = self.shape.cpos
        self.shape.csize = (2*self.radius, 2*self.radius)
        self.middle_pos = (Window.width / 2, Window.height * 7 / 8)

    def on_jump(self):
        if not self.is_jumping:
            self.animator = KFAnim((0, self.shape.cpos[1]),
                                   (0.0625, self.shape.cpos[1] + 1.5 * self.radius),
                                   (0.13, self.shape.cpos[1] + 2 * self.radius),
                                   (0.1925, self.shape.cpos[1] + 1.5 * self.radius),
                                   (0.25, self.shape.cpos[1]))
            self.time = 0
            self.is_jumping = True


    def on_key_down(self, color_letter):
        if color_letter == "r":
            self.color.rgb = (1, 0, 0)

        elif color_letter == "g":
            self.color.rgb = (0, 1, 0)

        elif color_letter == "b":
            self.color.rgb = (0, 0, 1)


        elif color_letter == "y":
            self.color.rgb = (1, 1, 0.5)


    def on_update(self, dt):

        if self.is_jumping:
            if not self.animator.is_active(self.time):
                self.is_jumping = False
                self.shape.cpos = (self.shape.cpos[0], self.middle_pos[1])
            else:
                cur_value = self.animator.eval(self.time)
                self.shape.cpos = (self.shape.cpos[0], cur_value)
                self.time += dt

        dx_dt = Window.width / movement_time
        dtheta_dt = dx_dt / self.radius
        self.rotation.angle -= dtheta_dt * (180 / np.pi) * dt
        self.rotation.origin = self.shape.cpos

class FakeColorSection(InstructionGroup):
    def __init__(self, position, length, height, color, game_widget=None):
        super(FakeColorSection, self).__init__()
        self.length = length
        self.orig_width = Window.width
        self.position = position
        self.game_widget = game_widget
        self.height = height
        self.orig_height = Window.height

        self.color = Color(color.rgb[0], color.rgb[1], color.rgb[2])
        self.big_rect = Rectangle(pos=(position[0], position[1]), size=(self.length, self.height))
        self.small_rect = Rectangle(pos=(-100, -100))
        self.line = Line(points=[0, 0, 0, 0], width=2)
        self.line.points = [self.position[0], self.position[1], self.position[0], self.position[1]+self.height]

        if self.color.rgb == [0, 1, 0]:
            self.small_rect.pos = (self.position[0], self.position[1] + self.height * 3 / 4)
            self.small_rect.size = (self.length, self.height * 1 / 4)

        elif self.color.rgb == [1, 0, 0]:
            self.small_rect.pos = (self.position[0], self.position[1] + self.height * 2 / 4)
            self.small_rect.size = (self.length, self.height * 1 / 4)

        elif self.color.rgb == [1, 1, 0.5]:
            self.small_rect.pos = (self.position[0], self.position[1] + self.height * 1 / 4)
            self.small_rect.size = (self.length, self.height * 1 / 4)

        elif self.color.rgb == [0, 0, 1]:
            self.small_rect.pos = (self.position[0], self.position[1])
            self.small_rect.size = (self.length, self.height * 1 / 4)

        self.add(self.color)
        self.add(self.line)
        self.color_big_rect = Color(self.color.rgb[0], self.color.rgb[1], self.color.rgb[2], 0.2)
        self.color_small_rect = Color(self.color.rgb[0], self.color.rgb[1], self.color.rgb[2], 0.25)

        self.add(self.color_big_rect)
        self.add(self.big_rect)
        self.add(self.color_small_rect)
        self.add(self.small_rect)

    def on_resize(self):
        # print(Window.width, self.orig_width)

        self.big_rect.pos = (self.position[0] * Window.width/self.orig_width, self.position[1] * Window.height/self.orig_height)
        if self.color.rgb == [0, 1, 0]:
            self.small_rect.pos = (self.position[0] * Window.width / self.orig_width, (self.position[1] + self.height * 3 / 4) * Window.height / self.orig_height)

        elif self.color.rgb == [1, 0, 0]:
            self.small_rect.pos = (self.position[0] * Window.width / self.orig_width, (self.position[1] + self.height * 2 / 4) * Window.height / self.orig_height)

        elif self.color.rgb == [1, 1, 0.5]:
            self.small_rect.pos = (self.position[0] * Window.width / self.orig_width, (self.position[1] + self.height * 1 / 4) * Window.height / self.orig_height)

        elif self.color.rgb == [0, 0, 1]:
            self.small_rect.pos = (self.position[0] * Window.width / self.orig_width, self.position[1] * Window.height / self.orig_height)

        self.big_rect.size = (self.length * Window.width / self.orig_width, self.height * Window.height / self.orig_height)
        self.small_rect.size = (self.length * Window.width / self.orig_width, self.height * Window.height / (4 * self.orig_height))

        self.line.points = [self.position[0] * Window.width / self.orig_width, self.position[1] * Window.height / self.orig_height,
                            self.position[0] * Window.width / self.orig_width, (self.position[1]+self.height) * Window.height / self.orig_height]

"""
Gameplay Objects
"""

class BeatLine(InstructionGroup):
    def __init__(self, start, dur, position, game_widget=None, jump=False):
        super(BeatLine, self).__init__()
        self.start = start
        self.dur = dur
        self.position = position # game_widget.line_positions[position]
        self.game_widget = game_widget
        self.color = Color(1, 1, 1)
        if jump:
            self.color = Color(128/255, 128/255, 128/255)

        self.line = Line(width=3)

        self.add(self.color)
        self.add(self.line)


    def on_update(self, now_time):
        x0 = Window.width/2
        dx_dt = (Window.width / movement_time)
        xf = dx_dt * (self.start - now_time) + x0

        self.line.points = [xf, self.game_widget.line_positions[self.position], xf + dx_dt*self.dur, self.game_widget.line_positions[self.position]]


        return (xf < Window.width and 0 < xf + dx_dt*self.dur < Window.width) or (xf < Window.width and xf + dx_dt*self.dur > Window.width)

class ColorSection(InstructionGroup):
    def __init__(self, start, dur, position, color, beatimes=None, game_widget=None):
        super(ColorSection, self).__init__()
        self.start = start
        self.dur = dur
        self.position = position
        self.game_widget = game_widget
        self.position = position
        self.y_position = game_widget.line_positions[self.position] + 3

        self.color = Color(color.rgb[0], color.rgb[1], color.rgb[2])
        self.big_rect = Rectangle(pos=(-100, -100))
        self.small_rect = Rectangle(pos=(-100, -100))
        self.line = Line(points=[0, 0, 0, 0], width=2)

        self.add(self.color)
        self.add(self.line)
        self.color_big_rect = Color(self.color.rgb[0], self.color.rgb[1], self.color.rgb[2], 0.2)
        self.color_small_rect = Color(self.color.rgb[0], self.color.rgb[1], self.color.rgb[2], 0.25)

        self.add(self.color_big_rect)
        self.add(self.big_rect)
        self.add(self.color_small_rect)
        self.add(self.small_rect)

        self.time = 0
        self.beatimes = beatimes
        if beatimes:
            key_frames = []
            for i, beat in enumerate(beatimes):
                key_frames.append((beat, self.y_position + (Window.height/8) * 1.15))
                if i + 1 < len(beatimes) - 1:
                    key_frames.append((beat + (beatimes[i+1] - beat)*3/4 , self.y_position + (Window.height*2.75/32)*1.15))

            self.animator=KFAnim(*key_frames)

        self.hit = False
        self.is_missed = False

    def on_resize(self):
        self.y_position = self.game_widget.line_positions[self.position] + 3
        if self.beatimes:
            key_frames = []
            for i, beat in enumerate(self.beatimes):
                key_frames.append((beat, self.y_position + (Window.height/8) * 1.15))
                if i + 1 < len(self.beatimes) - 1:
                    key_frames.append((beat + (self.beatimes[i+1] - beat)*3/4, self.y_position + (Window.height*2.75/32)*1.15))

            self.animator=KFAnim(*key_frames)

    def on_game_update(self, now_time):
        x0 = Window.width/2
        dx_dt = (Window.width / movement_time)
        xf = dx_dt * (self.start - now_time) + x0

        self.y_position = self.game_widget.line_positions[self.position] + 3

        if self.is_missed or song_select.song_file_name == "Through the Fire and Flames":
            self.line.points = [xf, self.y_position, xf, self.y_position + (Window.height/8) * 1.15]

            self.big_rect.pos = (xf, self.y_position)
            self.big_rect.size = (dx_dt * self.dur, (Window.height/8)*1.15)

            if self.color.rgb == [0, 1, 0]:
                # self.line.points = [xf, self.y_position + (self.animator.eval(now_time)-self.y_position) * 3 / 4, xf, self.animator.eval(now_time)]

                self.small_rect.pos = (xf, self.y_position + ((Window.height/8)*1.15) * 3 / 4)
                self.small_rect.size = (dx_dt * self.dur, ((Window.height/8)*1.15) * 1 / 4)

            elif self.color.rgb == [1, 0, 0]:
                # self.line.points = [xf, self.y_position + (self.animator.eval(now_time)-self.y_position) * 2 / 4, xf, self.y_position + (self.animator.eval(now_time)-self.y_position) * 3 / 4]

                self.small_rect.pos = (xf, self.y_position + ((Window.height/8)*1.15) * 2 / 4)
                self.small_rect.size = (dx_dt * self.dur, ((Window.height/8)*1.15) * 1 / 4)

            elif self.color.rgb == [1, 1, 0.5]:
                # self.line.points = [xf, self.y_position + (self.animator.eval(now_time)-self.y_position) * 1 / 4, xf, self.y_position + (self.animator.eval(now_time)-self.y_position) * 2 / 4]

                self.small_rect.pos = (xf, self.y_position + ((Window.height/8)*1.15) * 1 / 4)
                self.small_rect.size = (dx_dt * self.dur, ((Window.height/8)*1.15) * 1 / 4)

            elif self.color.rgb == [0, 0, 1]:
                # self.line.points = [xf, self.y_position, xf, self.y_position + (self.animator.eval(now_time)-self.y_position) * 1 / 4]

                self.small_rect.pos = (xf, self.y_position)
                self.small_rect.size = (dx_dt * self.dur, ((Window.height/8)*1.15) * 1 / 4)

            else:
                self.small_rect.size = (0,0)


        # WARNING VERY COSTLY PERFORMANCE WISE REMOVE IF NECESSARY
        else:
            self.line.points = [xf, self.y_position, xf, self.animator.eval(now_time)]
            if self.color.rgb == [0, 1, 0]:
                # self.line.points = [xf, self.y_position + (self.animator.eval(now_time)-self.y_position) * 3 / 4, xf, self.animator.eval(now_time)]


                self.small_rect.pos = (xf, self.y_position + (self.animator.eval(now_time)-self.y_position) * 3 / 4)
                self.small_rect.size = (dx_dt * self.dur, (self.animator.eval(now_time)-self.y_position) * 1 / 4)

            elif self.color.rgb == [1, 0, 0]:
                # self.line.points = [xf, self.y_position + (self.animator.eval(now_time)-self.y_position) * 2 / 4, xf, self.y_position + (self.animator.eval(now_time)-self.y_position) * 3 / 4]


                self.small_rect.pos = (xf, self.y_position + (self.animator.eval(now_time) - self.y_position) * 2 / 4)
                self.small_rect.size = (dx_dt * self.dur, (self.animator.eval(now_time) - self.y_position) * 1 / 4)

            elif self.color.rgb == [1, 1, 0.5]:
                # self.line.points = [xf, self.y_position + (self.animator.eval(now_time)-self.y_position) * 1 / 4, xf, self.y_position + (self.animator.eval(now_time)-self.y_position) * 2 / 4]


                self.small_rect.pos = (xf, self.y_position + (self.animator.eval(now_time) - self.y_position) * 1 / 4)
                self.small_rect.size = (dx_dt * self.dur, (self.animator.eval(now_time) - self.y_position) * 1 / 4)

            elif self.color.rgb == [0, 0, 1]:
                # self.line.points = [xf, self.y_position, xf, self.y_position + (self.animator.eval(now_time)-self.y_position) * 1 / 4]


                self.small_rect.pos = (xf, self.y_position)
                self.small_rect.size = (dx_dt * self.dur, (self.animator.eval(now_time) - self.y_position) * 1 / 4)


            # self.line.points = [xf, self.y_position, xf, self.animator.eval(now_time)]
            self.big_rect.pos = (xf, self.y_position)
            self.big_rect.size = (dx_dt*self.dur, self.animator.eval(now_time)-self.y_position)

        if (self.hit == False and self.is_missed == False) and self.start+0.1 < now_time < self.start+self.dur-0.025 and self.game_widget.player.color.rgb != self.color.rgb:
            #print("You Messed Up!")
            self.color.rgb = (0.5, 0.5, 0.5)
            self.color_big_rect.rgb = (0.5, 0.5, 0.5)
            self.game_widget.health_and_score.health -= 0.1
            self.is_missed = True
            self.game_widget.audio_ctrl.play_miss()
            self.game_widget.audio_ctrl.set_mute(0.1)
            self.game_widget.combo = 0
            self.game_widget.miss_count += 1

        elif self.is_missed == False and not self.hit and now_time > self.start+self.dur:
            self.game_widget.audio_ctrl.set_mute(0.3)
            self.hit = True
            self.game_widget.combo += 1
            self.game_widget.max_combo = max(self.game_widget.combo, self.game_widget.max_combo)
            self.game_widget.health_and_score.score += 100 * self.game_widget.combo
            self.game_widget.section_count += 1



        return 0 <= xf <= Window.width or 0 <= xf + dx_dt * self.dur <= Window.width

class SpikeObject(InstructionGroup):
    def __init__(self, start, position, game_widget=None):
        super(SpikeObject, self).__init__()
        self.start = start
        self.game_widget = game_widget
        self.position = position
        self.y_position = self.game_widget.line_positions[self.position] + 3

        self.color = Color(1,1,1)
        self.triangle = Triangle()

        self.add(PushMatrix())
        self.add(self.color)
        self.rotation = Rotate(angle=0)
        self.add(self.rotation)
        self.add(self.triangle)

        self.add(PopMatrix())
        self.is_passed = False

    def on_update(self, now_time):
        x0 = Window.width / 2
        dx_dt = (Window.width / movement_time)
        xf = dx_dt * (self.start - now_time) + x0

        self.y_position = self.game_widget.line_positions[self.position] + 3

        self.triangle.points = [xf, self.y_position, xf + dx_dt*0.075, self.y_position + Window.width/32, xf + dx_dt * 0.15, self.y_position]
        self.rotation.origin = (self.triangle.points[0], self.triangle.points[1])

        if not self.is_passed and self.start - 0.05 < self.game_widget.player.last_jumptime < self.start+0.1:
            self.is_passed = True
            self.game_widget.combo += 1
            self.game_widget.max_combo = max(self.game_widget.combo, self.game_widget.max_combo)
            self.game_widget.health_and_score.score += 100 * self.game_widget.combo
            self.game_widget.audio_ctrl.play_jump()
            self.game_widget.audio_ctrl.set_mute(0.3)
            self.game_widget.spike_count += 1
        elif not self.is_passed and now_time - self.start > 0.1:
            # print("You Messed Upoo")
            self.game_widget.audio_ctrl.play_miss()
            self.game_widget.audio_ctrl.set_mute(0.1)
            self.y_position -= 10
            self.rotation.angle -= 0.25
            self.color.rgb = [0.5,0.5,0.5]
            self.is_passed = True
            self.game_widget.health_and_score.health -= 0.2
            self.game_widget.combo = 0
            self.game_widget.miss_count += 1

        return 0 < self.triangle.points[0] < Window.width or 0 < self.triangle.points[4] < Window.width

class PlayerObject(InstructionGroup):
    def __init__(self, start_position, game_widget=None):
        super(PlayerObject, self).__init__()
        self.game_widget = game_widget


        self.color = Color(1,1,1)
        self.color.rgba = (1, 1, 1, 0.9)
        self.radius = Window.width/32
        self.position = start_position
        self.last_position = start_position
        self.player = CEllipse(cpos=(Window.width/2 - self.radius, game_widget.line_positions[self.position] + self.radius + 3), csize=(2*self.radius, 2*self.radius))
        self.player.segments = self.game_widget.segments
        self.add(PushMatrix())
        self.add(self.color)
        self.rotation = Rotate(angle=0, origin=self.player.cpos)
        self.add(self.rotation)
        self.add(self.player)

        self.add(PopMatrix())

        self.is_jumping = False
        self.time = None
        self.animator = None

        self.is_jump_zone=False
        self.last_jumptime = 0

    def on_key_down(self, color_letter):
        if color_letter == "r":
            self.color.rgb = (1, 0, 0)

        elif color_letter == "g":
            self.color.rgb = (0, 1, 0)

        elif color_letter == "b":
            self.color.rgb = (0, 0, 1)


        elif color_letter == "y":
            self.color.rgb = (1, 1, 0.5)




    def on_jump(self, now_time):
        if self.is_jumping == False:
            if not self.is_jump_zone and not self.is_jumping:
                # print(self.player.cpos[1])
                self.animator = KFAnim((0, self.player.cpos[1]),
                                       (0.0625, self.player.cpos[1] + 1.75 * self.radius),
                                       (0.13, self.player.cpos[1] + 2.5 * self.radius),
                                       (0.1925, self.player.cpos[1] + 1.75 * self.radius),
                                       (0.25, self.player.cpos[1]))
                self.time = 0
                self.is_jumping = True
            elif self.is_jump_zone and not self.is_jumping:
                self.game_widget.audio_ctrl.set_mute(0.3)
                self.game_widget.audio_ctrl.play_jump()
                self.game_widget.combo += 1
                self.game_widget.max_combo = max(self.game_widget.combo, self.game_widget.max_combo)
                self.game_widget.health_and_score.score += 100 * self.game_widget.combo
                self.game_widget.jumpline_count += 1
                self.last_position = self.position
                self.position = self.game_widget.current_jump_to_position
                delta = (self.game_widget.current_jumpline.start + self.game_widget.current_jumpline.dur) - self.game_widget.audio_ctrl.get_time() + 0.2
                if self.last_position < self.position:
                    self.animator = KFAnim((0, self.player.cpos[1]),
                                           (delta/3, self.game_widget.line_positions[self.position] + self.radius + 3),
                                          (delta*2/3, self.game_widget.line_positions[self.position] + 2*self.radius + 3),
                                          (delta, self.game_widget.line_positions[self.position] + self.radius + 3))
                else:
                    self.animator = KFAnim((0, self.player.cpos[1]),
                                           (delta / 3, self.player.cpos[1] + 2 * self.radius),
                                           (delta * 2 / 3, self.player.cpos[1]),
                                           (delta, self.game_widget.line_positions[self.position] + self.radius + 3))


                if self.game_widget.jumplines:
                    self.game_widget.current_jumpline = self.game_widget.jumplines.pop(0)
                    self.game_widget.current_jump_to_position = self.game_widget.jump_to_positions.pop(0)
                else:
                    self.game_widget.current_jumpline = None
                    self.game_widget.current_jump_to_position = None


                self.time = 0
                self.is_jumping = True

            self.last_jumptime = now_time

    def on_resize(self):
        self.radius = Window.width / 32
        self.player.cpos = (Window.width / 2 - self.radius, self.game_widget.line_positions[self.position] + self.radius + 3)
        self.player.csize = (2*self.radius, 2*self.radius)



    def on_update(self, dt):
        dx_dt = Window.width / movement_time
        if self.game_widget.current_jumpline:
            if self.game_widget.current_jumpline.line.points[0] < self.player.cpos[0] < self.game_widget.current_jumpline.line.points[2] + dx_dt*0.15:
                self.is_jump_zone = True
            else:
                if self.player.cpos[0] > self.game_widget.current_jumpline.line.points[2] and self.last_position == self.position:
                    self.game_widget.audio_ctrl.play_miss()
                    self.game_widget.audio_ctrl.set_mute(0.1)
                    self.game_widget.health_and_score.health -= 0.4
                    self.game_widget.combo = 0
                    if self.game_widget.health_and_score.health > 0:
                        self.game_widget.audio_ctrl.song.reset()
                        self.game_widget.audio_ctrl.toggle()
                    # print("You Messed Up!!!")
                    #
                    # self.last_position = self.game_widget.current_jump_to_position
                    # self.position = self.game_widget.current_jump_to_position
                    # if self.game_widget.jumplines:
                    #     self.game_widget.current_jumpline = self.game_widget.jumplines.pop(0)
                    #     self.game_widget.current_jump_to_position = self.game_widget.jump_to_positions.pop(0)
                    # else:
                    #     self.game_widget.current_jumpline = None
                    #     self.game_widget.current_jump_to_position = None
                    # self.player.cpos = (self.player.cpos[0], self.game_widget.line_positions[self.position] + self.radius + 3)
                    # self.is_jumping = False

                self.is_jump_zone = False
        else:
            self.is_jump_zone = False


        if self.is_jumping:
            if not self.animator.is_active(self.time):
                self.is_jumping = False
                self.last_position = self.position
                self.player.cpos = (self.player.cpos[0], self.game_widget.line_positions[self.position] + self.radius + 3)
            else:
                cur_value = self.animator.eval(self.time)

                self.player.cpos = (self.player.cpos[0], cur_value)

                self.time += dt

        self.rotation.origin = self.player.cpos
        dx_dt = Window.width/movement_time
        dtheta_dt = dx_dt / self.radius
        self.rotation.angle -= dtheta_dt*(180/np.pi) * dt

class ButtonDisplay(InstructionGroup):
    def __init__(self, lane, color):
        super(ButtonDisplay, self).__init__()
        self.lane =lane
        self.color = color
        self.color.rgba = [0.5, 0.5, 0.5, 1]

        self.button_colors = [[0, 1, 0, 0.2], [1, 0, 0, 0.2], [1, 1, 0.5, 0.2], [0, 0, 1, 0.2]]
        self.button_color = Color(0, 0, 0)
        self.button_color.rgba = self.button_colors[lane]

        nowbar_w_margin = 0.3
        nowbar_h = 0.15

        lane_positions = [nowbar_w_margin * Window.width + (1-2*nowbar_w_margin)*Window.width/3 * i for i in range(4)]
        inner_r = 0.25 * (1-2*nowbar_w_margin)*Window.width/4

        iterations = 1000
        # self.outer_circle = Line(points=[(inner_r*np.cos(2*np.pi*i/iterations) + lane_positions[lane], inner_r*np.sin(2*np.pi*i/iterations) + nowbar_h * Window.height) for i in range(iterations)], width =3)
        self.outer_circle = Line(circle=(lane_positions[lane], nowbar_h * Window.height, inner_r), width=2.5)
        self.inner_circle = CEllipse(cpos=(lane_positions[lane],nowbar_h * Window.height), csize=(2*inner_r,2*inner_r), segments = 40)

        self.add(self.button_color)
        self.add(self.inner_circle)
        self.add(self.color)
        self.add(self.outer_circle)



    # displays when button is pressed down
    def on_down(self):
        self.button_color.rgba[3] = 0.8

    # back to normal state
    def on_up(self):
        self.button_color.rgba[3] = 0.2

    # modify object positions based on new window size
    def on_resize(self, win_size):
        nowbar_w_margin = 0.3
        nowbar_h = 0.15

        lane_positions = [nowbar_w_margin * Window.width + (1 - 2 * nowbar_w_margin) * Window.width / 3 * i for i in range(4)]

        outer_r = 0.3 * (1 - 2 * nowbar_w_margin) * Window.width / 4
        inner_r = 0.25 * (1 - 2 * nowbar_w_margin) * Window.width / 4

        iterations = 1000
        self.outer_circle.points = [(inner_r*np.cos(2*np.pi*i/iterations) + lane_positions[self.lane], inner_r*np.sin(2*np.pi*i/iterations) + nowbar_h * Window.height) for i in range(iterations)]

        self.inner_circle.cpos = (lane_positions[self.lane], nowbar_h * Window.height)
        self.inner_circle.csize = (2 * inner_r, 2 * inner_r)

class PauseScreen(InstructionGroup):
    def __init__(self, game_widget=None):
        super(PauseScreen, self).__init__()
        self.rect = CRectangle(cpos=(Window.width/2, Window.height/2), csize=(2*max(Window.height, Window.width), 2*max(Window.height, Window.width)))
        self.color = Color(0, 0, 0)
        self.game_widget = game_widget

        self.color.rgba = [0, 0, 0, 0.85]

        self.add(self.color)
        self.add(self.rect)

        self.text_color = Color(1, 1, 1)

        self.pause_label = MovingLabel(cpos=(Window.width / 2, Window.height * 6 / 8), text="Pause",
                                 font_size=40)


        self.retry_label = MovingLabel(cpos=(Window.width / 2, Window.height * 4 / 8), text="Retry",
                                       font_size=20)

        self.song_select_label = MovingLabel(cpos=(Window.width / 2, Window.height * 3 / 8), text="Song Selection",
                                          font_size=20)

        self.title_screen_label = MovingLabel(cpos=(Window.width / 2, Window.height * 2 / 8), text="Title Screen",
                                    font_size=20)

        self.add(self.text_color)
        self.add(self.pause_label)
        self.add(self.song_select_label)
        self.add(self.retry_label)
        self.add(self.title_screen_label)
        self.original_height = Window.height

    def on_resize(self):
        self.rect.cpos, self.rect.csize = (Window.width/2, Window.height/2), (2*max(Window.height, Window.width), 2*max(Window.height, Window.width))

        for option in [self.pause_label, self.song_select_label, self.retry_label, self.title_screen_label, self.text_color]:
            self.remove(option)

        self.pause_label = MovingLabel(cpos=(Window.width / 2, Window.height * 6 / 8), text="Pause",
                                       font_size=40 * Window.height/self.original_height)

        self.retry_label = MovingLabel(cpos=(Window.width / 2, Window.height * 4 / 8), text="Retry",
                                       font_size=20 * Window.height / self.original_height)

        self.song_select_label = MovingLabel(cpos=(Window.width / 2, Window.height * 3 / 8), text="Song Selection",
                                             font_size=20 * Window.height/self.original_height)

        self.title_screen_label = MovingLabel(cpos=(Window.width / 2, Window.height * 2 / 8), text="Title Screen",
                                              font_size=20 *  Window.height/self.original_height)

        self.add(self.text_color)
        self.add(self.pause_label)
        self.add(self.song_select_label)
        self.add(self.retry_label)
        self.add(self.title_screen_label)

    def on_update(self):
        for option in [self.song_select_label, self.retry_label, self.title_screen_label]:
            if inside(Window.mouse_pos, option.cpos, option.label.texture_size):
                self.remove(option)
                self.add(Color(0.5, 0.5, 0.5))
                self.add(option)
            else:
                self.remove(option)
                self.add(Color(1, 1, 1))
                self.add(option)

    def on_touch_up(self, touch):
        for option in [self.song_select_label, self.retry_label, self.title_screen_label]:
            if inside(touch.pos, option.cpos, option.label.texture_size):
                if option.label.text == "Song Selection":
                    self.game_widget.switch_to("songselect")
                elif option.label.text == "Retry":
                    self.game_widget.switch_to("gamedisplayscreen")
                elif option.label.text == "Title Screen":
                    self.game_widget.switch_to("main")

class HealthScoreDisplay(InstructionGroup):
    def __init__(self, game_widget=None):
        super(HealthScoreDisplay, self).__init__()
        self.game_widget = game_widget

        self.health_box = Line(points=[0, Window.height*15/16, Window.width*5/16, Window.height*15/16,
                                       Window.width*5/16, Window.height], width=1)

        self.health_bar = Rectangle(pos=(0, Window.height*15/16), size=(Window.width*5/16, Window.height/16))

        self.score_label = CLabelRect(text="0", font_size=40,
                             cpos=(Window.width*7/8, Window.height*31/32))

        self.combo_label = CLabelRect(text=f"{self.game_widget.combo}x", font_size=40,
                                      cpos=(Window.width * 0.75 / 8, Window.height * 1 / 31))

        self.progress = 0

        # self.clock = Line(circle=(Window.width/2, Window.height*31/32 - 2, Window.height/32 - 4, 0, 360*self.progress))
        self.clock = CEllipse(cpos=(Window.width/2, Window.height*31/32 - 2), angle_start=0, angle_end=1,
                              csize=(2*(Window.height/32 - 4), 2*(Window.height/32 - 4)))
        self.score = 0

        while self.score_label.rect.pos[0] + self.score_label.rect.size[0] > Window.width:
            self.score_label.cpos = (self.score_label.cpos[0]-1, self.score_label.cpos[1])
            self.score_label.rect.pos = (self.score_label.rect.pos[0]-1, self.score_label.rect.pos[1])



        self.add(Color(115/255, 147/255, 179/255))
        self.add(self.health_bar)
        self.add(Color(1, 1, 1))
        self.add(self.health_box)
        self.add(self.score_label)
        self.add(self.combo_label)
        self.add(self.clock)

        self.health = 1

    def on_resize(self):
        self.score_label.cpos = (Window.width * 7 / 8, Window.height * 31 / 32)

        while self.score_label.rect.pos[0] + self.score_label.rect.size[0] > Window.width:
            self.score_label.cpos = (self.score_label.cpos[0]-10, self.score_label.cpos[1])
            self.score_label.rect.pos = (self.score_label.rect.pos[0]-10, self.score_label.rect.pos[1])

        self.health_bar.pos, self.health_bar.size = (0, Window.height*15/16), (Window.width*5/16*self.health, Window.height/16)
        self.health_box.points = [0, Window.height*15/16, Window.width*5/16, Window.height*15/16,
                                       Window.width*5/16, Window.height]

        self.combo_label.cpos = (Window.width * 0.75 / 8, Window.height * 1 / 31)
        self.clock.cpos, self.clock.angle_end, self.clock.csize = (Window.width / 2, Window.height * 31 / 32 - 2), 360*self.progress, (2 * (Window.height / 32 - 4), 2 * (Window.height / 32 - 4))

    def on_update(self):
        # self.score += 10
        self.score_label.set_text(str(self.score))
        self.combo_label.set_text(f"{self.game_widget.combo}x")
        if self.health <= 0:
            # self.game_widget.switch_to("gameover")
            self.game_widget.is_dead = True

        self.health = max(0, self.health)
        self.health += 0.05 * 0.017
        self.health = min(1, self.health)
        self.health_bar.pos, self.health_bar.size = (0, Window.height * 15 / 16), (Window.width * (5 / 16) * self.health, Window.height / 16)

        self.clock.angle_end = 360*self.progress

class DeathExplosion(InstructionGroup):
    def __init__(self, game_widget=None):
        super(DeathExplosion, self).__init__()

        self.game_widget = game_widget
        self.cpos = self.game_widget.player.player.cpos
        self.radius = self.game_widget.player.radius/3
        self.piece_1 = CEllipse(cpos=self.cpos, csize = (2*self.radius, 2*self.radius), segments=self.game_widget.segments)
        self.piece_2 = CEllipse(cpos=self.cpos, csize = (2*self.radius, 2*self.radius), segments=self.game_widget.segments)
        self.piece_3 = CEllipse(cpos=self.cpos, csize = (2*self.radius, 2*self.radius), segments=self.game_widget.segments)

        self.color = Color(0.5, 0.5, 0.5)

        self.add(self.color)
        self.add(self.piece_1)
        self.add(self.piece_2)
        self.add(self.piece_3)

    def on_update(self):
        dt = kivyClock.frametime
        dx_dt = 2*(Window.width / movement_time)
        self.piece_1.cpos = [self.piece_1.cpos[0] + dx_dt * dt, self.piece_1.cpos[1] + np.sin(np.pi/6)*dx_dt*dt]
        self.piece_2.cpos = [self.piece_2.cpos[0] + dx_dt * dt, self.piece_2.cpos[1]]
        self.piece_3.cpos = [self.piece_3.cpos[0] + dx_dt * dt, self.piece_3.cpos[1] - np.sin(np.pi/6)*dx_dt*dt]


"""
Screens
"""

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.segments = 4
        self.index = 0
        self.segment_list = [4, 3, 5, 8]


        self.audio = Audio(2)

        self.info = topleft_label()
        self.add_widget(self.info)

        self.color = Color(1,1,1)
        self.objects = AnimGroup()
        self.canvas.add(self.objects)
        self.objects.add(self.color)


        # initializing the several menu options
        self.title = MovingLabel(cpos=(Window.width / 2, Window.height * 6 / 8), text="BeatCourse",
                                font_size=40)
        self.song_selection = MovingLabel(cpos=(Window.width / 2, Window.height * 4 / 8), text="Song Selection",
                                         font_size=20)
        # self.settings = MovingLabel(cpos=(Window.width / 2, Window.height * 3 / 8), text="Settings",
        #                            font_size=20)

        self.spinning_object = SpinningObject(position=(Window.width / 2, Window.height * 7 / 8), main_widget=self)
        self.left_triangle = Triangle()
        self.right_triangle = Triangle()

        self.objects.add(self.spinning_object)
        self.canvas.add(Color(1,1,1))
        self.canvas.add(self.left_triangle)
        self.canvas.add(self.right_triangle)
        self.objects.add(self.title)
        self.objects.add(self.song_selection)
        # self.objects.add(self.settings)
        self.original_height = Window.height

    def on_enter(self):
        # random song to play
        self.song_file_names = [filename for filename in os.listdir("songs/") if filename != ".DS_Store"]
        chosen_song = np.random.choice(self.song_file_names)
        print(chosen_song)
        self.audio_ctrl = AudioController(song_folder_path="songs/" + chosen_song, main_widget=self)
        self.last_song = chosen_song
        self.last_frames = []
        self.last_frames.append(self.audio_ctrl.song.frame)
        self.audio_ctrl.toggle()

    def on_resize(self, win_size):
        resize_topleft_label(self.info)

        self.spinning_object.on_resize()
        self.left_triangle.points = [self.spinning_object.middle_pos[0] - 1*self.spinning_object.shape.csize[0], self.spinning_object.middle_pos[1] + 0.3*self.spinning_object.shape.csize[0],
                                     self.spinning_object.middle_pos[0] - 1*self.spinning_object.shape.csize[0], self.spinning_object.middle_pos[1] - 0.3*self.spinning_object.shape.csize[0],
                                     self.spinning_object.middle_pos[0] - 1.5*self.spinning_object.shape.csize[0], self.spinning_object.middle_pos[1]]

        self.right_triangle.points = [self.spinning_object.middle_pos[0] + 1 * self.spinning_object.shape.csize[0], self.spinning_object.middle_pos[1] + 0.3 * self.spinning_object.shape.csize[0],
                                      self.spinning_object.middle_pos[0] + 1 * self.spinning_object.shape.csize[0], self.spinning_object.middle_pos[1] - 0.3 * self.spinning_object.shape.csize[0],
                                      self.spinning_object.middle_pos[0] + 1.5 * self.spinning_object.shape.csize[0], self.spinning_object.middle_pos[1]]


        for option in [self.title, self.song_selection]:
            self.objects.remove(option)
        self.objects.add(self.color)

        self.title = MovingLabel(cpos=(Window.width / 2, Window.height * 6 / 8), text="BeatCourse",
                                font_size=40 * Window.height/self.original_height)
        self.song_selection = MovingLabel(cpos=(Window.width / 2, Window.height * 4 / 8), text="Song Selection",
                                         font_size=20 * Window.height/self.original_height)
        # self.settings = MovingLabel(cpos=(Window.width / 2, Window.height * 3 / 8), text="Settings",
        #                            font_size=20 * Window.height/self.original_height)

        self.objects.add(self.title)
        self.objects.add(self.song_selection)
        # self.objects.add(self.settings)

    def on_touch_up(self, touch):
        for option in [self.song_selection]:
            if inside(touch.pos, option.cpos, option.label.texture_size):
                if option.label.text == "Song Selection":
                    self.switch_to("songselect")
                # elif option.label.text == "Settings":
                #     print("Not Implemented")

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == "spacebar":
            self.spinning_object.on_jump()

        elif keycode[1] == "left":
            self.index -= 1
            self.index = self.index % len(self.segment_list)
            self.segments = self.segment_list[self.index]
            self.spinning_object.shape.segments = self.segments

        elif keycode[1] == "right":
            self.index += 1
            self.index = self.index % len(self.segment_list)
            self.segments = self.segment_list[self.index]
            self.spinning_object.shape.segments = self.segments




    def on_update(self):

        self.audio_ctrl.on_update()
        self.audio.on_update()
        self.last_frames.append(self.audio_ctrl.song.frame)

        if len(self.last_frames) == 10:
            if len(set(self.last_frames)) == 1 and 0 not in set(self.last_frames):
                chosen_song = np.random.choice(self.song_file_names)
                while chosen_song == self.last_song:
                    chosen_song = np.random.choice(self.song_file_names)
                # print(chosen_song)
                self.last_song = chosen_song
                self.audio_ctrl = AudioController(song_folder_path="songs/" + chosen_song, main_widget=self)
                self.last_frames = []
                self.last_frames.append(self.audio_ctrl.song.frame)
                self.audio_ctrl.toggle()
            else:
                self.last_frames.pop(0)



        self.objects.on_update()
        self.info.text = ""
        for option in [self.song_selection]:
            if inside(Window.mouse_pos, option.cpos, option.label.texture_size):
                self.objects.remove(option)
                self.objects.add(Color(0.5, 0.5, 0.5))
                self.objects.add(option)
            else:
                self.objects.remove(option)
                self.objects.add(Color(1, 1, 1))
                self.objects.add(option)
        # print(self.canvas.length())

class GameDisplayScreen(Screen):
    def __init__(self, **kwargs):
        super(GameDisplayScreen, self).__init__(**kwargs)
        self.buttons = None
        self.is_paused = False
        self.health_and_score = None
        self.line_positions = [Window.height / 4, Window.height * 2 / 4, Window.height * 3 / 4]
        self.color_sections = None
        self.player = None
        self.is_dead = False
        self.explosion = None
        self.combo = 0
        self.max_combo = 0
        self.section_count = 0
        self.spike_count = 0
        self.jumpline_count = 0
        self.miss_count = 0




    def on_resize(self, win_size):
        self.line_positions = [Window.height / 4, Window.height * 2 / 4, Window.height * 3 / 4]
        if self.health_and_score:
            self.health_and_score.on_resize()

        if self.buttons:
            for i in range(4):
                self.buttons[i].on_resize(win_size)

        if self.color_sections:
            for color_section in self.color_sections:
                color_section.on_resize()

        if self.player:
            self.player.on_resize()

        if self.is_paused:
            self.pause.on_resize()

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == 'backspace':
            self.switch_to("songselect")

        color_letter = lookup(keycode[1], 'fghj', ("g", "r", "y", "b"))
        button_idx = lookup(keycode[1], 'fghj', (0, 1, 2, 3))
        if color_letter and not self.is_paused:
            self.player.on_key_down(color_letter)
            self.buttons[button_idx].on_down()

        if keycode[1] == "spacebar" and not self.is_paused:
            # print("hello")
            self.player.on_jump(self.audio_ctrl.get_time())

        if keycode[1] == "p":
            # self.audio_ctrl.song.reset()
            # self.audio_ctrl.toggle()
            if not self.is_paused:
                self.canvas.add(self.pause)
                self.is_paused = True
            else:
                self.canvas.remove(self.pause)
                self.is_paused = False


    def on_key_up(self, keycode):
        button_idx = lookup(keycode[1], 'fghj', (0, 1, 2, 3))
        if button_idx is not None:
            self.buttons[button_idx].on_up()

    def on_touch_up(self, touch):
        if self.is_paused:
            self.pause.on_touch_up(touch)

    def on_enter(self):
        self.combo = 0
        self.max_combo = 0
        self.section_count = 0
        self.spike_count = 0
        self.jumpline_count = 0
        self.miss_count = 0
        self.segments = main.segments
        self.audio_ctrl = AudioController(song_folder_path="songs/" + song_select.song_file_name, main_widget=self)
        self.audio_ctrl.toggle()

        self.info = topleft_label()
        self.add_widget(self.info)

        self.objects = AnimGroup()
        self.canvas.add(self.objects)

        self.beatlines = []
        self.color_sections = []
        self.beat_data = SongData("songs/"+ song_select.song_file_name +"/notes.tsv").get_beats()

        last_position = None
        last_beatline = None

        first_position = None

        self.jump_to_positions = []
        self.jumplines = []

        color_map = {0: Color(0, 1, 0),
                     1: Color(1, 0, 0),
                     2: Color(1, 1, 0.5),
                     3: Color(0, 0, 1)}

        self.spikes = []

        self.barlines = []

        self.buttons = []

        self.alt_set = set()

        for i in range(4):
            button = ButtonDisplay(i, Color(1, 1, 1))
            self.canvas.add(button)
            self.buttons.append(button)

        self.health_and_score = HealthScoreDisplay(self)
        self.canvas.add(self.health_and_score)
        self.pause = PauseScreen(self)


        self.canvas.add(PushMatrix())
        self.rotation = Rotate(angle=0)
        self.canvas.add(self.rotation)

        for beat_tuple in self.beat_data:
            if beat_tuple[1] == "N":
                if beat_tuple[2] in [2, 3, 4]:
                    beatline = BeatLine(beat_tuple[0], beat_tuple[3], 4 - beat_tuple[2], self)
                    if first_position is None:
                        first_position = 4 - beat_tuple[2]
                        self.player = PlayerObject(first_position, self)
                        self.objects.add(self.player)
                    self.beatlines.append(beatline)
                    self.canvas.add(beatline)

                    if last_position is not None:
                        self.jump_to_positions.append(4 - beat_tuple[2])
                        jump_line = BeatLine(beat_tuple[0] - min(0.3,last_beatline.dur) , min(0.3,last_beatline.dur), last_position, self, jump=True)
                        self.beatlines.append(jump_line)
                        self.jumplines.append(jump_line)

                        self.canvas.add(jump_line)

                    last_position = 4 - beat_tuple[2]
                    last_beatline = beatline
                    # print(last_position)

                elif beat_tuple[2] in [0, 1]:
                    if beat_tuple[0] in self.alt_set:
                        color_section = ColorSection(beat_tuple[0], beat_tuple[3], last_position,
                                                     color_map[beat_tuple[2] + 2], self.barlines, self)
                    else:
                        color_section = ColorSection(beat_tuple[0], beat_tuple[3], last_position, color_map[beat_tuple[2]], self.barlines, self)
                    self.color_sections.append(color_section)
                    self.canvas.add(color_section)

                elif beat_tuple[2] in [6]:
                    self.alt_set.add(beat_tuple[0])


                elif beat_tuple[2] in [7]:
                    spike_time = beat_tuple[0]
                    spike = SpikeObject(spike_time, last_position, self)
                    self.canvas.add(spike)
                    self.spikes.append(spike)
            elif beat_tuple[1] == "B":
                self.barlines.append(beat_tuple[0])

        if self.jumplines:
            self.current_jumpline = self.jumplines.pop(0)
            self.current_jump_to_position = self.jump_to_positions.pop(0)
        else:
            self.current_jumpline = None
            self.current_jump_to_position = None

        if self.jumplines:
            self.total_time = self.beatlines[-2].start + self.beatlines[-2].dur
        else:
            self.total_time = self.beatlines[-1].start + self.beatlines[-1].dur





    def on_exit(self):
        self.canvas.clear()
        self.is_paused = False
        self.is_dead = False
        self.explosion = None

    def on_update(self):
        if not self.is_paused and not self.is_dead:
            self.rotation.angle -= 0.0
            self.rotation.origin = self.player.player.cpos
            self.audio_ctrl.on_update()
            now = self.audio_ctrl.get_time()
            self.health_and_score.on_update()
            self.health_and_score.progress = now / self.total_time
            # print(self.health_and_score.progress)
            if self.health_and_score.progress >= 1:
                df = pd.read_csv("scores.csv", header=0)

                is_inside = False
                for index, row in df.iterrows():
                    if row['song'] == song_select.song_file_name:
                        if row['score'] < self.health_and_score.score:
                            df.at[index, 'score'] = self.health_and_score.score
                        is_inside = True

                if not is_inside:
                    df_row = pd.DataFrame({"song": song_select.song_file_name, "score": self.health_and_score.score}, index=[len(df)])
                    df = pd.concat([df, df_row], axis=0)

                df.to_csv("scores.csv", index=False)
                self.switch_to("gamewin")
            self.game_update(now)
            self.objects.on_update()


        elif self.is_paused:
            self.pause.on_update()
        elif self.is_dead:
            self.audio_ctrl.on_update()
            now = self.audio_ctrl.get_time()
            if self.player in self.objects.children:
                self.objects.remove(self.player)
            if not self.explosion:
                self.explosion = DeathExplosion(self)
                self.canvas.add(self.explosion)
            self.explosion.on_update()

            if self.explosion.piece_1.cpos[0] > Window.width+10:
                self.switch_to("gameover")


        # print(self.canvas.length(), len(self.beatlines), len(self.color_sections), len(self.spikes))


    def game_update(self, now_time):
        # print(self.max_combo)
        # print(self.health_and_score.score)
        self.info.text = ''

        for i, beatline in enumerate(self.beatlines):
            vis = beatline.on_update(now_time)
            if vis and beatline not in self.canvas.children:
                self.canvas.add(beatline)
            # elif i != 0 and not vis and beatline in self.canvas.children:
            #     self.canvas.remove(beatline)

        for spike in self.spikes:
            vis = spike.on_update(now_time)
            if vis and spike not in self.canvas.children:
                self.canvas.add(spike)
            elif not vis and spike in self.canvas.children:
                self.canvas.remove(spike)

        for color_section in self.color_sections:
            vis = color_section.on_game_update(now_time)
            if vis and color_section not in self.canvas.children:
                self.canvas.add(color_section)
            elif not vis and color_section in self.canvas.children:
                self.canvas.remove(color_section)

class SongSelectionScreenDisplay(Screen):
    def __init__(self, **kwargs):
        super(SongSelectionScreenDisplay, self).__init__(**kwargs)
        # self.main_widget = main_widget
        self.image = None
        self.song_file_names = [filename for filename in os.listdir("songs/") if filename != ".DS_Store"]

        # initializes a general song selection menu that can be expanded depending on song file folder contents
        self.canvas.add(Color(1, 1, 1))
        self.delta = (Window.height/8)
        prev_pos = (Window.width / 4, Window.height * 7 / 8 + self.delta)
        self.label_rects = []
        self.top_position = Window.height * 7 / 8
        self.top_line = Line(points=[Window.width / 4 - Window.width/6 - 10, self.top_position + self.delta/2 + 10, Window.width / 4 + Window.width/6 + 10, self.top_position + self.delta/2 + 10], width=3)
        self.canvas.add(self.top_line)
        self.borders = []
        self.color_dict = {}
        for song in self.song_file_names:
            x0, y0 = prev_pos[0], prev_pos[1] - self.delta
            i = 20

            # tries to resize the text so that it fits "reasonably" well
            while CLabelRect(cpos=(x0, y0), text=song, font_size=i).label.texture_size[0] > Window.width/3:
                i -= 1

            label_rect = CLabelRect(cpos=(x0, y0), text=song,
                       font_size=i)
            x1, y1 = x0 - Window.width/6 - 10, y0 + self.delta/2 + 10
            x2, y2 = x0 - Window.width/6 - 10, y0 - self.delta/2 - 10
            x3, y3 = x0 + Window.width/6 + 10, y0 - self.delta/2 - 10
            x4, y4 = x0 + Window.width/6 + 10, y0 + self.delta/2 + 10
            border = Line(points=[x1, y1, x2, y2, x3, y3, x4, y4], width=3)

            self.label_rects.append(label_rect)
            self.borders.append(border)
            self.color_dict[song] = [Color(1, 1, 1), Color(1, 1, 1)]
            self.canvas.add(self.color_dict[song][0])
            self.canvas.add(label_rect)
            self.canvas.add(self.color_dict[song][1])
            self.canvas.add(border)
            prev_pos = (x0, y0)

        self.song_name = None
        self.artist = None
        self.album = None
        self.charter = None
        self.song_file_name = None
        self.highscore = None
        self.orig_height = Window.height

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == "down":
            self.on_shift("down")
        elif keycode[1] == "up":
            self.on_shift("up")
        elif keycode[1] == "backspace":
            self.switch_to("main")

    def on_exit(self):
        if self.image:
            self.remove_widget(self.image)
            self.image = None

    def on_touch_up(self, touch):
        for option in self.label_rects:
            # checks if the mouse is on a song in the select screen and determines what to do if a touch up
            if inside(touch.pos, option.cpos, (Window.height / 3 + 20, Window.height / 8 + 20)):
                self.song_file_name = option.label.text
                if option.label.text == "Signs (Jump Tutorial)":
                    self.switch_to("jump")
                elif option.label.text == "Moonlight Sonata 1st. Mvt (Color Section Tutorial)":
                    self.switch_to("color")
                else:
                    self.switch_to("gamedisplayscreen")

    def on_shift(self, direction):
        """
        handles shifting the song selection menu if trying to access other options not visible
        """
        self.canvas.remove(self.top_line)
        for rect in self.label_rects:
            self.canvas.remove(rect)
        for border in self.borders:
            self.canvas.remove(border)
        self.canvas.add(Color(1, 1, 1))
        if direction == "up":
            self.top_position -= self.delta
        elif direction == "down":
            self.top_position += self.delta

        self.top_position = min(self.top_position, Window.height + (len(self.song_file_names) - 8) * self.delta)
        self.top_position = max(self.top_position, 7 *self.delta)

        prev_pos = (Window.width / 4, self.top_position + self.delta)
        self.label_rects = []
        self.top_line = Line(points=[Window.width / 4 - Window.width / 6 - 10, self.top_position + self.delta / 2 + 10,
                                     Window.width / 4 + Window.width / 6 + 10, self.top_position + self.delta / 2 + 10],
                             width=3)
        self.canvas.add(self.top_line)
        self.borders = []
        for song in self.song_file_names:
            x0, y0 = prev_pos[0], prev_pos[1] - self.delta
            i = 20
            while CLabelRect(cpos=(x0, y0), text=song, font_size=i).label.texture_size[0] > Window.width / 3:
                i -= 1

            label_rect = CLabelRect(cpos=(x0, y0), text=song,
                                    font_size=i)
            x1, y1 = x0 - Window.width / 6 - 10, y0 + self.delta / 2 + 10
            x2, y2 = x0 - Window.width / 6 - 10, y0 - self.delta / 2 - 10
            x3, y3 = x0 + Window.width / 6 + 10, y0 - self.delta / 2 - 10
            x4, y4 = x0 + Window.width / 6 + 10, y0 + self.delta / 2 + 10
            border = Line(points=[x1, y1, x2, y2, x3, y3, x4, y4], width=3)

            self.label_rects.append(label_rect)
            self.borders.append(border)
            self.canvas.add(label_rect)
            self.canvas.add(border)
            prev_pos = (x0, y0)

    def on_resize(self, win_size):
        """
        handles resizing song selection menu
        """
        self.canvas.clear()

        self.canvas.add(Color(1, 1, 1))
        self.delta = (Window.height / 8)
        self.top_position = min(self.top_position, Window.height + (len(self.song_file_names) - 8) * self.delta)
        self.top_position = max(self.top_position, 7 * self.delta)
        prev_pos = (Window.width / 4, self.top_position + self.delta)
        self.label_rects = []
        self.top_line = Line(points=[Window.width / 4 - Window.width / 6 - 10, self.top_position + self.delta / 2 + 10,
                                     Window.width / 4 + Window.width / 6 + 10, self.top_position + self.delta / 2 + 10],
                             width=3)
        self.canvas.add(self.top_line)
        self.borders = []
        for song in self.song_file_names:
            x0, y0 = prev_pos[0], prev_pos[1] - self.delta
            i = 20
            while CLabelRect(cpos=(x0, y0), text=song, font_size=i).label.texture_size[0] > Window.width / 3:
                i -= 1

            label_rect = CLabelRect(cpos=(x0, y0), text=song,
                                    font_size=i)
            x1, y1 = x0 - Window.width / 6 - 10, y0 + self.delta / 2 + 10
            x2, y2 = x0 - Window.width / 6 - 10, y0 - self.delta / 2 - 10
            x3, y3 = x0 + Window.width / 6 + 10, y0 - self.delta / 2 - 10
            x4, y4 = x0 + Window.width / 6 + 10, y0 + self.delta / 2 + 10
            border = Line(points=[x1, y1, x2, y2, x3, y3, x4, y4], width=3)

            self.label_rects.append(label_rect)
            self.borders.append(border)
            self.canvas.add(self.color_dict[song][0])
            self.canvas.add(label_rect)
            self.canvas.add(self.color_dict[song][1])
            self.canvas.add(border)
            prev_pos = (x0, y0)

        i=0
        temp_list = []
        for item in [self.song_name, self.artist, self.album, self.charter]:
            if item:
                temp_list.append(item)

        for item in temp_list:
            x = 20
            text = item.label.text

            while CLabelRect(cpos=(0, 0), text=text, font_size=x).label.texture_size[0] > Window.width * 4 / 16:
                x -= 1

            if i == 0:
                if self.song_name:
                    self.canvas.remove(self.song_name)
                self.song_name = CLabelRect(cpos=(Window.width * 19 / 32, Window.width * 3 / 16), text=text, font_size=x)
                self.canvas.add(self.song_name)

            if i == 1:
                if self.artist:
                    self.canvas.remove(self.artist)
                self.artist = CLabelRect(cpos=(Window.width * 27 / 32, Window.width * 3 / 16), text=text, font_size=x)
                self.canvas.add(self.artist)

            if i == 2:
                if self.album:
                    self.canvas.remove(self.album)
                self.album = CLabelRect(cpos=(Window.width * 19 / 32, Window.width * 1 / 8), text=text, font_size=x)
                self.canvas.add(self.album)

            if i == 3:
                if self.charter:
                    self.canvas.remove(self.charter)
                self.charter = CLabelRect(cpos=(Window.width * 27 / 32, Window.width * 1 / 8), text=text, font_size=x)
                self.canvas.add(self.charter)

            i += 1

        if self.image:
            self.image.width = Window.width * 7 / 16
            self.image.height = Window.height * 4 / 8
            self.image.pos = (Window.width * 4 / 8, Window.height * 3 / 8)

    def on_update(self):
        """
        handles displaying song info, color change for labels, and album image
        """
        mouse_pos = Window.mouse_pos
        is_image = self.image is not None
        for option in self.label_rects:
            if inside(mouse_pos, option.cpos, (Window.height/3 + 20, Window.height/8 + 20)):
                if self.image:
                    self.remove_widget(self.image)
                    self.image = None
                self.color_dict[option.label.text][0].rgb = [0.5, 0.5, 0.5]

                song_folder_path = "songs"

                for filename in os.listdir(song_folder_path +"/" + option.label.text):
                    if len(filename) >= 5 and filename[:5] == "album":
                        if is_image:
                            self.remove_widget(self.image)
                            self.image = None
                        self.image = Image(source=song_folder_path +"/" + option.label.text + "/" + filename, fit_mode="fill")
                        self.image.color = [1, 1, 1, 1]
                        self.image.width = Window.width * 7/16
                        self.image.height = Window.height * 4/8
                        self.image.pos = (Window.width * 4/8, Window.height * 3/8)
                        self.add_widget(self.image, index=-1)
                        is_image = True
                        break

                name = None
                artist = None
                album = None
                charter = None

                with open(song_folder_path+"/" + option.label.text+"/song.ini",  encoding="utf8") as f:
                    for line in f.readlines():
                        split_line = line.strip().split(' ')
                        if split_line[0] == "Name:":
                            name = " ".join(line.strip().split(' '))
                        if split_line[0] == "Artist:":
                            artist = " ".join(line.strip().split(' '))
                        if split_line[0] == "Album:":
                            album = " ".join(line.strip().split(' '))
                        if split_line[0] == "Charter:":
                            charter = " ".join(line.strip().split(' '))

                df = pd.read_csv("scores.csv", header=0)

                is_inside = False
                if self.highscore:
                    self.canvas.remove(self.highscore)
                for index, row in df.iterrows():
                    if row['song'] == option.label.text:
                        self.highscore = CLabelRect(cpos=(Window.width * (1/2 + 7/32), Window.height * 15 / 16), text=f"Best Score: {row['score']}",
                                                 font_size=20*Window.height/self.orig_height)

                        self.canvas.add(self.highscore)
                        is_inside = True

                if not is_inside:
                    self.highscore = CLabelRect(cpos=(Window.width * (1/2 + 7/32), Window.height * 15 / 16),
                                                text=f"Best Score: {0}",
                                                font_size=20*Window.height/self.orig_height)
                    self.canvas.add(self.highscore)

                i=0
                for item in [name, artist, album, charter]:
                    x = 20

                    if item:
                        text = item
                    else:
                        text = ""

                    while CLabelRect(cpos=(0, 0), text=text, font_size=x).label.texture_size[0] > Window.width* 4 / 16:
                        x -= 1

                    if i == 0:
                        if self.song_name:
                            self.canvas.remove(self.song_name)
                        self.song_name = CLabelRect(cpos=(Window.width*19/32, Window.height*2/8), text=text, font_size=x)
                        self.canvas.add(self.song_name)

                    if i == 1:
                        if self.artist:
                            self.canvas.remove(self.artist)
                        self.artist = CLabelRect(cpos=(Window.width*27/32, Window.height*2/8), text=text, font_size=x)
                        self.canvas.add(self.artist)

                    if i == 2:
                        if self.album:
                            self.canvas.remove(self.album)
                        self.album = CLabelRect(cpos=(Window.width*19/32, Window.height*1/8), text=text, font_size=x)
                        self.canvas.add(self.album)

                    if i == 3:
                        if self.charter:
                            self.canvas.remove(self.charter)
                        self.charter = CLabelRect(cpos=(Window.width*27/32, Window.height*1/8), text=text, font_size=x)
                        self.canvas.add(self.charter)

                    i+= 1


            else:
                self.color_dict[option.label.text][0].rgb = [1, 1, 1]
        # print(self.canvas.length())

class GameOverScreen(Screen):
    def __init__(self, **kwargs):
        super(GameOverScreen, self).__init__(**kwargs)


        self.audio = Audio(2)

        self.info = topleft_label()
        self.add_widget(self.info)

        self.color = Color(1,1,1)
        self.objects = AnimGroup()
        self.canvas.add(self.objects)
        self.objects.add(self.color)

        # initializing the several menu options
        self.gameover_label = MovingLabel(cpos=(Window.width / 2, Window.height * 6 / 8), text="Game Over",
                                font_size=40)
        self.retry_label = MovingLabel(cpos=(Window.width / 2, Window.height * 4 / 8), text="Retry",
                                       font_size=20)
        self.song_select_label = MovingLabel(cpos=(Window.width / 2, Window.height * 3 / 8), text="Song Selection",
                                         font_size=20)
        self.titlescreen_label = MovingLabel(cpos=(Window.width / 2, Window.height * 2 / 8), text="Title Screen",
                                   font_size=20)

        self.objects.add(self.titlescreen_label)
        self.objects.add(self.song_select_label)
        self.objects.add(self.gameover_label)
        self.original_height = Window.height

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == "backspace":
            self.switch_to("songselect")

    def on_resize(self, win_size):
        resize_topleft_label(self.info)

        for option in [self.gameover_label, self.retry_label, self.song_select_label, self.titlescreen_label]:
            self.objects.remove(option)

        self.gameover_label = MovingLabel(cpos=(Window.width / 2, Window.height * 6 / 8), text="Game Over",
                                          font_size=40*Window.height/self.original_height)
        self.retry_label = MovingLabel(cpos=(Window.width / 2, Window.height * 4 / 8), text="Retry",
                                       font_size=20*Window.height/self.original_height)
        self.song_select_label = MovingLabel(cpos=(Window.width / 2, Window.height * 3 / 8), text="Song Selection",
                                             font_size=20*Window.height/self.original_height)
        self.titlescreen_label = MovingLabel(cpos=(Window.width / 2, Window.height * 2 / 8), text="Title Screen",
                                             font_size=20*Window.height/self.original_height)

        self.objects.add(self.titlescreen_label)
        self.objects.add(self.song_select_label)
        self.objects.add(self.gameover_label)
        self.objects.add(self.retry_label)

    def on_touch_up(self, touch):
        for option in [self.retry_label, self.song_select_label, self.titlescreen_label]:
            if inside(touch.pos, option.cpos, option.label.texture_size):
                if option.label.text == "Song Selection":
                    self.switch_to("songselect")
                elif option.label.text == "Retry":
                    self.switch_to("gamedisplayscreen")
                elif option.label.text == "Title Screen":
                    self.switch_to("main")



    def on_update(self):

        self.audio.on_update()
        self.objects.on_update()
        self.info.text = ""
        for option in [self.retry_label, self.song_select_label, self.titlescreen_label]:
            if inside(Window.mouse_pos, option.cpos, option.label.texture_size):
                self.objects.remove(option)
                self.objects.add(Color(0.5, 0.5, 0.5))
                self.objects.add(option)
            else:
                self.objects.remove(option)
                self.objects.add(Color(1, 1, 1))
                self.objects.add(option)

class GameWinScreen(Screen):
    def __init__(self, **kwargs):
        super(GameWinScreen, self).__init__(**kwargs)


        self.audio = Audio(2)

        self.info = topleft_label()
        self.add_widget(self.info)

        self.color = Color(1, 1, 1)
        self.objects = AnimGroup()

        # initializing the several menu options
        self.gamewin_label = MovingLabel(cpos=(Window.width / 2, Window.height * 7 / 8), text="You Win!",
                                font_size=40)


        self.score_label = MovingLabel(cpos=(Window.width / 4, Window.height * 13 / 16),
                                       text=f"Your Score: {0}",
                                       font_size=30)
        self.combo_label = MovingLabel(text=f"{0}x", font_size=40,
                                      cpos=(Window.width * 1 / 4, Window.height * 4 / 16))



        self.retry_label = MovingLabel(cpos=(Window.width * 3 / 4, Window.height * 4 / 8), text="Retry",
                                       font_size=20)
        self.song_select_label = MovingLabel(cpos=(Window.width * 3 / 4, Window.height * 3 / 8), text="Song Selection",
                                         font_size=20)
        self.titlescreen_label = MovingLabel(cpos=(Window.width * 3 / 4, Window.height * 2 / 8), text="Title Screen",
                                   font_size=20)

        self.green_section = FakeColorSection((Window.width / 8, Window.height * 10 / 16),
                                              Window.height / 16, Window.height / 16, Color(0, 1, 0), self)
        self.section_count_label = MovingLabel(cpos=(Window.width / 4, Window.height * 10.25 / 16),
                                       text=f"0",
                                       font_size=40)

        dx_dt = (Window.width / movement_time)
        self.spike = Triangle(points=[Window.width / 8, Window.height * 8 / 16,
                                      Window.width / 8 + dx_dt * 0.075, Window.height * 8 / 16 + Window.height / 32,
                                      Window.width / 8 + dx_dt * 0.15, Window.height * 8 / 16])

        self.spike_count_label = MovingLabel(cpos=(Window.width / 4, Window.height * 8.25 / 16),
                                               text=f"0",
                                               font_size=40)

        self.miss_color = Color(1, 0, 0)

        self.miss = MovingLabel(cpos=(Window.width * 5/ 32, Window.height * 6.25 / 16),
                                               text=f"X",
                                               font_size=40)

        self.miss_count_label = MovingLabel(cpos=(Window.width / 4, Window.height * 6.25 / 16),
                                               text=f"0",
                                               font_size=40)

        self.score_stats_bg = Rectangle(pos=(Window.width / 16, Window.height * 3 / 16),
                                        size=(Window.width * 4 / 8, Window.height * 11 / 16))


        self.canvas.add(Color(0.5, 0.5, 0.5, 0.7))
        self.canvas.add(self.score_stats_bg)
        self.canvas.add(self.miss_color)
        self.objects.add(self.miss)
        self.canvas.add(self.green_section)
        self.canvas.add(Color(1, 1, 1))
        self.canvas.add(self.spike)
        self.canvas.add(self.objects)
        self.objects.add(self.color)
        self.objects.add(self.score_label)
        self.objects.add(self.combo_label)
        self.objects.add(self.titlescreen_label)
        self.objects.add(self.song_select_label)

        self.objects.add(self.section_count_label)
        self.objects.add(self.spike_count_label)
        self.objects.add(self.miss_count_label)

        self.objects.add(self.gamewin_label)
        self.original_height = Window.height
        self.boolean = False

    def on_enter(self):
        self.on_resize(None)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == "backspace":
            self.switch_to("songselect")

    def on_resize(self, win_size):
        resize_topleft_label(self.info)
        self.green_section.on_resize()


        for option in [self.color, self.gamewin_label, self.score_label, self.retry_label, self.song_select_label, self.titlescreen_label,
                       self.section_count_label, self.spike_count_label, self.combo_label, self.miss_count_label, self.miss, self.miss_color]:
            self.objects.remove(option)

        self.gamewin_label = MovingLabel(cpos=(Window.width * 3 / 4, Window.height * 7 / 8), text="You Win!",
                                          font_size=40*Window.height/self.original_height)

        if gamedisplay.health_and_score:
            self.score_label = MovingLabel(cpos=(Window.width * 1 / 4, Window.height * 13 / 16),
                                           text=f"Your Score: {gamedisplay.health_and_score.score}",
                                           font_size=30*Window.height/self.original_height)

            self.combo_label = MovingLabel(text=f"{gamedisplay.max_combo}x", font_size=40*Window.height/self.original_height,
                                          cpos=(Window.width * 1 / 3, Window.height * 4 / 16))


        self.retry_label = MovingLabel(cpos=(Window.width * 3 / 4, Window.height * 4 / 8), text="Retry",
                                       font_size=20*Window.height/self.original_height)
        self.song_select_label = MovingLabel(cpos=(Window.width * 3 / 4, Window.height * 3 / 8), text="Song Selection",
                                             font_size=20*Window.height/self.original_height)
        self.titlescreen_label = MovingLabel(cpos=(Window.width * 3 / 4, Window.height * 2 / 8), text="Title Screen",
                                             font_size=20*Window.height/self.original_height)

        if gamedisplay.health_and_score:
            self.section_count_label = MovingLabel(cpos=(Window.width * 1 / 3, Window.height * 10.375 / 16),
                                                   text=f"{gamedisplay.section_count} / {len(gamedisplay.color_sections)}",
                                                   font_size=40*Window.height/self.original_height)

            self.spike_count_label = MovingLabel(cpos=(Window.width * 1 / 3, Window.height * 8.25 / 16),
                                                 text=f"{gamedisplay.spike_count} / {len(gamedisplay.spikes)}",
                                                 font_size=40*Window.height/self.original_height)

            self.miss_count_label = MovingLabel(cpos=(Window.width * 1 / 3, Window.height * 6.25 / 16),
                                                    text=f"{gamedisplay.miss_count} ",
                                                    font_size=40*Window.height/self.original_height)

            self.miss = MovingLabel(cpos=(Window.width * 5 / 32, Window.height * 6.25 / 16),
                                    text=f"X",
                                    font_size=40*Window.height/self.original_height)

        self.objects.add(self.color)
        self.objects.add(self.score_label)
        self.objects.add(self.combo_label)
        self.objects.add(self.titlescreen_label)
        self.objects.add(self.retry_label)
        self.objects.add(self.song_select_label)
        self.objects.add(self.gamewin_label)
        self.objects.add(self.section_count_label)
        self.objects.add(self.spike_count_label)
        self.objects.add(self.miss_count_label)
        self.objects.add(self.miss_color)
        self.objects.add(self.miss)

        self.score_stats_bg.pos = (Window.width / 16, Window.height * 3 / 16)
        self.score_stats_bg.size = (Window.width * 4 / 8, Window.height * 11 / 16)

        dx_dt = (Window.width / movement_time)
        self.spike.points = [Window.width / 8, Window.height * 8 / 16,
                                      Window.width / 8 + dx_dt * 0.075, Window.height * 8 / 16 + Window.height / 32,
                                      Window.width / 8 + dx_dt * 0.15, Window.height * 8 / 16]



    def on_touch_up(self, touch):

        for option in [self.retry_label, self.song_select_label, self.titlescreen_label]:
            if inside(touch.pos, option.cpos, option.label.texture_size):
                if option.label.text == "Song Selection":
                    self.switch_to("songselect")
                elif option.label.text == "Title Screen":
                    self.switch_to("main")
                elif option.label.text == "Retry":
                    self.switch_to("gamedisplayscreen")



    def on_update(self):
        if gamedisplay.health_and_score and not self.boolean:
            self.on_resize("None")
            self.boolean = True

        self.audio.on_update()
        self.objects.on_update()
        self.info.text = ""
        for option in [self.retry_label, self.song_select_label, self.titlescreen_label]:
            if inside(Window.mouse_pos, option.cpos, option.label.texture_size):
                self.objects.remove(option)
                self.objects.add(Color(0.5, 0.5, 0.5))
                self.objects.add(option)
            else:
                self.objects.remove(option)
                self.objects.add(Color(1, 1, 1))
                self.objects.add(option)


class JumpTutorialScreen(Screen):
    def __init__(self, **kwargs):
        super(JumpTutorialScreen, self).__init__(**kwargs)
        self.jump_label_1 = None
        self.original_height = Window.height

    def on_enter(self):
        self.objects = AnimGroup()
        self.canvas.add(self.objects)
        self.segments = main.segments
        text1 = "This is the Jump Tutorial. This beatcourse\n"
        text1 += "focuses on learning to avoid jumping-based\n"
        text1 += "obstacles such as jumplines and spikes.\n\n"
        text1 += "You can jump using the SPACEBAR\n\n"
        text1 += "For jumplines, you want to jump \n"
        text1 += "while inside. For spikes you will\n"
        text1 +=  "want to jump before the spike.\n\n"
        text1 +=  "An example of a spike (left) and a \n "
        text1 += "jumpline (right) are shown below:\n"
        self.jump_label_1 = CLabelRect(text=text1, font_size=17*Window.height/self.original_height, cpos=(Window.width*2/7, Window.height*4/7))
        self.canvas.add(Color(1, 1, 1))
        self.canvas.add(self.jump_label_1)

        text2 = "You can try pressing SPACEBAR here"
        self.jump_label_2 = CLabelRect(text=text2, font_size=17*Window.height/self.original_height, cpos=(Window.width*5/7, Window.height*6/8))
        self.canvas.add(Color(1, 1, 1))
        self.canvas.add(self.jump_label_2)

        text3 = "Jump Tutorial"
        self.jump_label_3 = CLabelRect(text=text3, font_size=25*Window.height/self.original_height, cpos=(Window.width * 1 / 2, Window.height * 7.5 / 8))
        self.canvas.add(Color(1, 1, 1))
        self.canvas.add(self.jump_label_3)

        self.spinning_object = SpinningObject(position=(Window.width* 23/ 32, Window.height* 1/ 2), main_widget=self)
        self.canvas.add(Color(1, 1, 1))
        self.objects.add(self.spinning_object)


        dx_dt = (Window.width / movement_time)
        self.spike = Triangle(points= [Window.width/8, Window.height/4, Window.width/8 + dx_dt*0.075, Window.height/4 + Window.height/32, Window.width/8 + dx_dt * 0.15, Window.height/4])

        self.jumpline = Line(points= [Window.width*2/8, Window.height/4, Window.width*3/8,  Window.height/4], width=3)

        text4 = "BEWARE! YOU WILL LOSE HEALTH AND COMBO IF YOU MISS A JUMP OBSTACLE!"
        self.jump_label_4 = CLabelRect(text=text4, font_size=18*Window.height/self.original_height, cpos=(Window.width * 1 / 2, Window.height * 0.5 / 8))
        self.canvas.add(Color(1, 0, 0))
        self.canvas.add(self.jump_label_4)

        text5 = "Press D to start ->"
        self.jump_label_5 = CLabelRect(text=text5, font_size=18*Window.height/self.original_height, cpos=(Window.width*5/7, Window.height*1.5/8))
        self.canvas.add(Color(0, 1, 0))
        self.canvas.add(self.jump_label_5)

        self.canvas.add(Color(1, 1, 1))
        self.canvas.add(self.spike)
        self.canvas.add(Color(0.5, 0.5, 0.5))
        self.canvas.add(self.jumpline)

    def on_resize(self, win_size):
        if self.jump_label_1:
            self.jump_label_1.cpos=(Window.width * 2 / 7, Window.height * 4 / 7)



            self.jump_label_2.cpos=(Window.width * 5 / 7, Window.height * 6 / 8)



            self.jump_label_3.cpos = (Window.width * 1 / 2, Window.height * 7.5 / 8)


            self.spinning_object.on_resize()
            self.spinning_object.shape.cpos = (Window.width* 23/ 32, Window.height* 1/ 2)
            self.spinning_object.middle_pos = (Window.width* 23/ 32, Window.height* 1/ 2)




            dx_dt = (Window.width / movement_time)
            self.spike.points=[Window.width / 8, Window.width / 8, Window.width / 8 + dx_dt * 0.075,
                                          Window.width / 8 + Window.width / 32, Window.width / 8 + dx_dt * 0.15,
                                          Window.width / 8]

            self.jumpline.points = [Window.width * 2 / 8, Window.width / 8, Window.width * 3 / 8, Window.width / 8]


            self.jump_label_4.cpos = (Window.width * 1 / 2, Window.height * 0.5 / 8)



            self.jump_label_5.cpos = (Window.width * 5 / 7, Window.height * 1.5 / 8)


    def on_key_down(self, keycode, modifiers):
        if keycode[1] == "spacebar":
            self.spinning_object.on_jump()

        elif keycode[1] == "backspace":
            self.switch_to("songselect")

        elif keycode[1] == "d":
            self.switch_to('gamedisplayscreen')


    def on_exit(self):
        self.canvas.clear()

    def on_update(self):
        self.objects.on_update()

class ColorTutorialScreen(Screen):
    def __init__(self, **kwargs):
        super(ColorTutorialScreen, self).__init__(**kwargs)
        self.color_label_1 = None
        self.original_height = Window.height
        self.green_section = None

    def on_enter(self):
        self.objects = AnimGroup()
        self.canvas.add(self.objects)
        self.segments = main.segments
        text1 = "This is the Color Section Tutorial. This beatcourse\n"
        text1 += "focuses on learning to beat color section\n"
        text1 += "obstacles.\n\n"
        text1 += "You can changes colors using FGHJ Buttons\n\n"
        text1 += "F corresponds to Green. G corresponds to Red.\n"
        text1 += "H corresponds to Yellow. J corresponds to Blue\n\n"
        text1 +=  "An example of a color section is show below. \n "
        text1 += "The position of the bar on the color section \n"
        text1 +=  "is meant to help with coordinating button presses.\n"
        self.color_label_1 = CLabelRect(text=text1, font_size=17*Window.height/self.original_height, cpos=(Window.width*2/7, Window.height*4/7))
        self.canvas.add(Color(1, 1, 1))
        self.canvas.add(self.color_label_1)

        text2 = "You can try changing colors here"
        self.color_label_2 = CLabelRect(text=text2, font_size=17*Window.height/self.original_height, cpos=(Window.width*5/7, Window.height*6/8))
        self.canvas.add(Color(1, 1, 1))
        self.canvas.add(self.color_label_2)

        text3 = "Color Section Tutorial"
        self.color_label_3 = CLabelRect(text=text3, font_size=25*Window.height/self.original_height, cpos=(Window.width * 1 / 2, Window.height * 7.5 / 8))
        self.canvas.add(Color(1, 1, 1))
        self.canvas.add(self.color_label_3)

        self.spinning_object = SpinningObject(position=(Window.width* 23/ 32, Window.height* 1/ 2), main_widget=self)
        self.canvas.add(Color(1, 1, 1))
        self.objects.add(self.spinning_object)

        self.green_section = FakeColorSection((Window.width/8 - Window.width/16, Window.height/4), Window.height/16, Window.height/16, Color(0, 1, 0), self)
        self.red_section = FakeColorSection((Window.width * 2 / 8 - Window.width/16, Window.height / 4), Window.height / 16, Window.height / 16, Color(1, 0, 0), self)
        self.yellow_section = FakeColorSection((Window.width * 3 / 8 - Window.width/16, Window.height / 4), Window.height / 16, Window.height / 16, Color(1, 1, 0.5), self)
        self.blue_section = FakeColorSection((Window.width * 4 / 8 - Window.width/16, Window.height / 4), Window.height / 16, Window.height / 16, Color(0, 0, 1), self)
        self.canvas.add(self.green_section)
        self.canvas.add(self.red_section)
        self.canvas.add(self.yellow_section)
        self.canvas.add(self.blue_section)



        text4 = "BEWARE! YOU WILL LOSE HEALTH AND COMBO IF YOU MISS A COLOR OBSTACLE!"
        self.color_label_4 = CLabelRect(text=text4, font_size=18*Window.height/self.original_height, cpos=(Window.width * 1 / 2, Window.height * 0.5 / 8))
        self.canvas.add(Color(1, 0, 0))
        self.canvas.add(self.color_label_4)

        text5 = "Press D to start ->"
        self.color_label_5 = CLabelRect(text=text5, font_size=18*Window.height/self.original_height, cpos=(Window.width*5/7, Window.height*1.5/8))
        self.canvas.add(Color(0, 1, 0))
        self.canvas.add(self.color_label_5)



    def on_resize(self, win_size):
        if self.green_section:
            self.green_section.on_resize()
            self.red_section.on_resize()
            self.blue_section.on_resize()
            self.yellow_section.on_resize()

        if self.color_label_1:
            self.color_label_1.cpos=(Window.width * 2 / 7, Window.height * 4 / 7)



            self.color_label_2.cpos=(Window.width * 5 / 7, Window.height * 6 / 8)



            self.color_label_3.cpos = (Window.width * 1 / 2, Window.height * 7.5 / 8)


            self.spinning_object.on_resize()
            self.spinning_object.shape.cpos = (Window.width* 23/ 32, Window.height* 1/ 2)
            self.spinning_object.middle_pos = (Window.width* 23/ 32, Window.height* 1/ 2)




            self.color_label_4.cpos = (Window.width * 1 / 2, Window.height * 0.5 / 8)



            self.color_label_5.cpos = (Window.width * 5 / 7, Window.height * 1.5 / 8)


    def on_key_down(self, keycode, modifiers):
        if keycode[1] == "spacebar":
            self.spinning_object.on_jump()

        elif keycode[1] == "backspace":
            self.switch_to("songselect")

        elif keycode[1] == "d":
            self.switch_to('gamedisplayscreen')

        color_letter = lookup(keycode[1], 'fghj', ("g", "r", "y", "b"))
        button_idx = lookup(keycode[1], 'fghj', (0, 1, 2, 3))
        if color_letter:
            self.spinning_object.on_key_down(color_letter)



    def on_exit(self):
        self.canvas.clear()

    def on_update(self):
        self.objects.on_update()



# remember: you might find ScreenManager helpful here!
sm = ScreenManager()

main = MainScreen(name='main')
song_select = SongSelectionScreenDisplay(name='songselect')
jump_tutorial = JumpTutorialScreen(name='jump')
color_tutorial = ColorTutorialScreen(name='color')
gamedisplay = GameDisplayScreen(name='gamedisplayscreen')
gameover = GameOverScreen(name="gameover")
gamewin = GameWinScreen(name="gamewin")

sm.add_screen(main)
sm.add_screen(song_select)
sm.add_screen(jump_tutorial)
sm.add_screen(color_tutorial)
sm.add_screen(gamedisplay)
sm.add_screen(gameover)
sm.add_screen(gamewin)

run(sm)
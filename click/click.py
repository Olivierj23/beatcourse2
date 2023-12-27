#####################################################################
#
# This software is to be used for MIT's class Interactive Music Systems only.
# Since this file may contain answers to homework problems, you MAY NOT release it publicly.
#
#####################################################################

import sys, os
sys.path.insert(0, os.path.abspath('..'))


from imslib.core import BaseWidget, run
from imslib.audio import Audio
from imslib.mixer import Mixer
from imslib.wavegen import WaveGenerator
from imslib.wavesrc import WaveFile

from kivy.clock import Clock as kivyClock
from kivy.core.window import Window
from kivy.graphics import Rectangle

class MainWidget(BaseWidget):
    def __init__(self):
        super(MainWidget, self).__init__()

        self.audio = Audio(2)
        self.mixer = Mixer()
        self.mixer.set_gain(0.75)
        self.audio.set_generator(self.mixer)

        self.click_wave = WaveFile('./click.wav')

        self.flash_timer = 0

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == 'spacebar':
            if self.flash_timer == 0:
                self.flash_timer = 0.3
                self.flash = Rectangle(pos=(0,0), size=(Window.width, Window.height), color=(1,1,1,0))
                self.canvas.add(self.flash)

                self.click_gen = WaveGenerator(self.click_wave)
                self.mixer.add(self.click_gen)

    def on_update(self):
        self.audio.on_update()

        if self.flash_timer > 0:
            self.flash_timer -= kivyClock.frametime
            if self.flash_timer <= 0:
                self.canvas.remove(self.flash)
                self.flash = None
                self.flash_timer = 0

if __name__ == "__main__":
    run(MainWidget())

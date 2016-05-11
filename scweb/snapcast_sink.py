from __future__ import division

import os

from scweb.player import Player, PlayerError


RATE = 44100
PERIODSIZE = 44100 / 40  # 0.025s
MAXPERIODS = int(0.5 * RATE / PERIODSIZE)  # 0.5s Buffer
NAMEDPIPE = '/tmp/snapfifo'


class SnapcastSink(Player):

    def __init__(self, namedpipe=NAMEDPIPE, buffer_length=MAXPERIODS):

        self._device = None
        self.namedpipe = namedpipe

        self._mixer = None

        super(SnapcastSink, self).__init__(buffer_length)

    def mixer_load(self, mixer="", volmin=0, volmax=100):
        # TODO: Implement mixer
        self.volmin = volmin
        self.volmax = volmax
        return

    def mixer_unload(self):
        self._mixer = None

    def acquire(self):
        try:
            self._device = os.open(self.namedpipe, os.O_WRONLY)
        except IOError as error:
            raise PlayerError("PlayerError: {}".format(error))

    def release(self):
        os.close(self._device)
        self._device = None

    def _write_data(self, data):
        os.write(self._device, data)

    def _getvolume(self):
        # TODO:Implement mixer
        return 100

    def _setvolume(self, volume):
        # TODO:Implement mixer
        pass

    def _getmute(self):
        # TODO:Implement mixer
        return False

    def _setmute(self, value):
        # TODO:Implement mixer
        pass

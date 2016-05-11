from __future__ import division

import re
import sys

import alsaaudio as alsa

from scweb.player import Player, PlayerError


RATE = 44100
CHANNELS = 2
PERIODSIZE = 44100 / 40  # 0.025s
MAXPERIODS = int(0.5 * RATE / PERIODSIZE)  # 0.5s Buffer


class AlsaSink(Player):

    def __init__(self, device='default', rate=RATE, channels=CHANNELS,
                 periodsize=PERIODSIZE, buffer_length=MAXPERIODS):
        self._device = None
        self.device_name = device
        self.rate = rate
        self.channels = channels
        self.periodsize = periodsize

        super(AlsaSink, self).__init__(buffer_length)

    def mixer_load(self, mixer="", volmin=0, volmax=100):
        # List cardindex for all devices
        card_info = {}
        for device_number, card_name in enumerate(alsa.cards()):
            card_info[card_name] = device_number

        # get Card Index for the device
        pattern = r'(\w+)+?:?(?:card=(\w+))?,?(?:dev=(\w+))?'
        result = re.match(pattern, self.device_name, re.IGNORECASE)
        cardname = result.group(2)
        device = result.group(3)

        if cardname is None:
            cardindex = -1
        else:
            cardindex = card_info[cardname]

        if device is None:
            device = 'default'

        if not mixer:
            try:
                device_mixers = alsa.mixers(device=device, cardindex=cardindex)
            except alsa.ALSAAudioError as error:
                raise PlayerError("PlayerError: {}".format(error))

            if len(device_mixers) > 0:
                mixer = device_mixers[0]
            else:
                raise PlayerError("PlayerError: Device has no mixers")
        try:
            self._mixer = alsa.Mixer(mixer, device=device, cardindex=cardindex)
        except alsa.ALSAAudioError as error:
            raise PlayerError("PlayerError: {}".format(error))

        self.volmin = volmin
        self.volmax = volmax

    def mixer_unload(self):
        self._mixer.close()
        self._mixer = None

    def acquire(self):
        try:
            if hasattr(alsa, 'pcms'):  # pyalsaaudio >= 0.8
                self._device = alsa.PCM(
                    alsa.PCM_PLAYBACK, device=self.device_name)
            else:  # pyalsaaudio == 0.7
                self._device = alsa.PCM(
                    alsa.PCM_PLAYBACK, card=self.device_name)
            if sys.byteorder == 'little':
                self._device.setformat(alsa.PCM_FORMAT_S16_LE)
            else:
                self._device.setformat(alsa.PCM_FORMAT_S16_BE)
            self._device.setchannels(self.channels)
            self._device.setrate(self.rate)
            self._device.setperiodsize(self.periodsize)

        except alsa.ALSAAudioError as error:
            raise PlayerError("PlayerError: {}".format(error))

    def release(self):
        self._device.close()
        self._device = None

    def _write_data(self, data):
        self._device.write(data)

    def _getvolume(self):
        return self._mixer.getvolume()[0]

    def _setvolume(self, volume):
        self._mixer.setvolume(volume)

    def _getmute(self):
        return self._mixer.getmute()[0]

    def _setmute(self, value):
        self._mixer.setmute(value)

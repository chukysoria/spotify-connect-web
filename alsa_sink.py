import Queue
import re
from threading import Thread, Event

import alsaaudio as alsa
from spotifyconnect import Sink


RATE = 44100
CHANNELS = 2
PERIODSIZE = 44100 / 40  # 0.025s
SAMPLESIZE = 2  # 16 bit integer
MAXPERIODS = int(0.5 * RATE / PERIODSIZE)  # 0.5s Buffer

pending_data = str()

class AlsaSink(Sink):


    def __init__(self, device, rate=RATE, channels=CHANNELS, periodsize=PERIODSIZE, buffer_length=MAXPERIODS):
        self.device = None
        self.device_name = device
        self.rate = rate
        self.channels = channels
        self.periodsize = periodsize

        self.mixer = None

        self.queue = Queue.Queue(maxsize=buffer_length)
        self.t = Thread()
        self.t.name = "AlsaSinkLoop"

        self.on()


    def _on_music_delivery(self, audio_format, samples, num_samples, pending, session):
        global pending_data

        buf = pending_data + samples

        try:
            total = 0
            while len(buf) >= PERIODSIZE * CHANNELS * SAMPLESIZE:
                self.write(buf[:PERIODSIZE * CHANNELS * SAMPLESIZE])
                buf = buf[PERIODSIZE * CHANNELS * SAMPLESIZE:]
                total += PERIODSIZE * CHANNELS

            pending_data = buf
            return num_samples
        except BufferFull:
            return total
        finally:
            pending[0] = self.buffer_length() * PERIODSIZE * CHANNELS

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
            self.mixer = alsa.Mixer(mixer, device=device, cardindex=cardindex)
        except alsa.ALSAAudioError as error:
            raise PlayerError("PlayerError: {}".format(error))

        self.volmin = volmin
        self.volmax = volmax

    def mixer_unload(self):
        self.mixer.close()
        self.mixer = None

    def mixer_loaded(self):
        if self.mixer is not None:
            return True
        else:
            return False

    def acquire(self):
        try:
            self.device = alsa.PCM(alsa.PCM_PLAYBACK, device=self.device_name)
            self.device.setchannels(self.channels)
            self.device.setrate(self.rate)
            self.device.setperiodsize(self.periodsize)
            self.device.setformat(alsa.PCM_FORMAT_S16_LE)
        except alsa.ALSAAudioError as error:
            raise PlayerError("PlayerError: {}".format(error))

    def release(self):
        self.device.close()
        self.device = None

    def acquired(self):
        if self.device is not None:
            return True
        else:
            return False

    def playback_thread(self, q, e):
        while not e.is_set():
            data = q.get()
            if data:
                self.device.write(data)
            q.task_done()

    def play(self):
        self.t_stop = Event()
        self.t = Thread(args=(self.queue, self.t_stop), target=self.playback_thread)
        self.t.daemon = True
        self.t.start()

    def pause(self):
        self.t_stop.set()

        if self.queue.empty():
            self.queue.put(str())

        self.t.join()

    def playing(self):
        if self.t.isAlive():
            return True
        else:
            return False

    def write(self, data):
        try:
            self.queue.put(data, block=False)
        except Queue.Full:
            raise BufferFull()

    def buffer_flush(self):
        while not self.queue.empty():
            self.queue.get()
            self.queue.task_done()

    def buffer_length(self):
        return self.queue.qsize()

    def volrange_set(self, volmin, volmax):
        self.volmin = volmin
        self.volmax = volmax

    def volume_get(self):
        mixer_volume = self.mixer.getvolume()[0]

        if mixer_volume > self.volmax:
            mixer_volume = self.volmax
        elif mixer_volume < self.volmin:
            mixer_volume = self.volmin

        volume = int(round((mixer_volume - self.volmin) / float(self.volmax - self.volmin) * 100))
        return volume

    def volume_set(self, volume):
        if volume == 0:
            self.mixer.setmute(1)
        else:
            if self.mixer.getmute()[0] == 1:
                self.mixer.setmute(0)
        mixer_volume = int(round((self.volmax - self.volmin) * volume / 100.0 + self.volmin))
        self.mixer.setvolume(mixer_volume)

class PlayerError(Exception):
    pass

class BufferFull(Exception):
    pass

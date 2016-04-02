import Queue
import os
import re
from threading import Thread, Event

from spotifyconnect import Sink


RATE = 44100
CHANNELS = 2
PERIODSIZE = 44100 / 40  # 0.025s
SAMPLESIZE = 2  # 16 bit integer
MAXPERIODS = int(0.5 * RATE / PERIODSIZE)  # 0.5s Buffer
NAMEDPIPE = '/tmp/snapfifo'

pending_data = str()

class SnapcastSink(Sink):


    def __init__(self, namedpipe=NAMEDPIPE, buffer_length=MAXPERIODS):
        
        self.pipe = None
        self.namedpipe = namedpipe

        self.mixer = None

        self.queue = Queue.Queue(maxsize=buffer_length)
        self.t = Thread()
        self.t.name = "SnapcastSinkLoop"

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
        ##TODO: Implement mixer
        return

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
            self.pipe = os.open(self.namedpipe, os.O_WRONLY)
        except IOError as error:
            raise PlayerError("PlayerError: {}".format(error))

    def release(self):
        os.close(self.pipe)
        self.pipe = None

    def acquired(self):
        if self.pipe is not None:
            return True
        else:
            return False

    def playback_thread(self, q, e):
        while not e.is_set():
            data = q.get()
            if data:
                os.write(self.pipe, data)
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
        #TODO:Implement mixer
        return 100

    def volume_set(self, volume):
        #TODO:Implement mixer
        return 100

class PlayerError(Exception):
    pass

class BufferFull(Exception):
    pass

try:
    # Python 3
    import queue
except ImportError:
    # Python 2
    import Queue as queue
from threading import Event, Thread

from spotifyconnect import Sink

CHANNELS = 2
PERIODSIZE = 44100 / 40  # 0.025s
SAMPLESIZE = 2  # 16 bit integer

pending_data = str()


class Player(Sink):

    def __init__(self, buffer_length):
        self.queue = queue.Queue(maxsize=buffer_length)
        self.t = Thread()
        self.t.name = "{0}Loop".format(type(self).__name__)

        self.on()

    _device = None
    _mixer = None

    def _on_music_delivery(self, audio_format, samples,
                           num_samples, pending, session):
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

    def mixer_load(self, mixer=None, volmin=0, volmax=100):
        raise NotImplementedError

    def mixer_unload(self):
        raise NotImplementedError

    def mixer_loaded(self):
        if self._mixer is not None:
            return True
        else:
            return False

    def acquire(self):
        raise NotImplementedError

    def _close(self):
        self.release()

    def release(self):
        raise NotImplementedError

    def acquired(self):
        if self._device is not None:
            return True
        else:
            return False

    def playback_thread(self, q, e):
        while not e.is_set():
            data = q.get()
            if data:
                self._write_data(data)
            q.task_done()

    def _write_data(self, data):
        raise NotImplementedError

    def play(self):
        self.t_stop = Event()
        self.t = Thread(
            args=(self.queue, self.t_stop), target=self.playback_thread)
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
        except queue.Full:
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
        mixer_volume = self._getvolume()

        if mixer_volume > self.volmax:
            mixer_volume = self.volmax
        elif mixer_volume < self.volmin:
            mixer_volume = self.volmin

        volume = int(round((mixer_volume - self.volmin) /
                           float(self.volmax - self.volmin) * 100))
        return volume

    def _getvolume(self):
        raise NotImplementedError

    def volume_set(self, volume):
        if volume == 0:
            self._setmute(True)
        else:
            if self._getmute():
                self._setmute(False)
        mixer_volume = int(round((self.volmax - self.volmin) *
                                 volume / 100.0 + self.volmin))
        self._setvolume(mixer_volume)

    def _setvolume(self, volume):
        raise NotImplementedError

    def _getmute(self):
        raise NotImplementedError

    def _setmute(self, value):
        raise NotImplementedError


class PlayerError(Exception):
    pass


class BufferFull(Exception):
    pass

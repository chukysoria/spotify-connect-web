import unittest

from tests import mock


import spotifyconnect
import sc_console.alsa_sink

class TestAlsaSink(unittest.TestCase):

    def setUp(self):
        self.session = mock.Mock()
        self.session.player.num_listeners.return_value = 0
        spotifyconnect._session_instance = self.session
        self.alsaaudio = mock.Mock()
        self.alsaaudio.pcms = mock.Mock()


        with mock.patch.dict('sys.modules', {'alsaaudio': self.alsaaudio}):
            self.sink = sc_console.alsa_sink.AlsaSink('default')

    def test_off_closes_audio_device(self):
        device_mock = mock.Mock()
        self.sink.device = device_mock

        self.sink.off()

        device_mock.close.assert_called_with()
        self.assertIsNone(self.sink.device)

    def test_defaults(self):
        self.assertEqual(self.sink.device_name, 'default')
        self.assertEqual(self.sink.rate, sc_console.alsa_sink.RATE)
        self.assertEqual(self.sink.channels, sc_console.alsa_sink.CHANNELS)
        self.assertEqual(self.sink.periodsize, sc_console.alsa_sink.PERIODSIZE)
        self.session.player.num_listeners.assert_called_once_with(spotifyconnect.PlayerEvent.MUSIC_DELIVERY)
 
    def test_initialization(self):        
        with mock.patch.dict('sys.modules', {'alsaaudio': self.alsaaudio}):
            self.sink = sc_console.alsa_sink.AlsaSink('other device', 100, 6, 0.43, 1348)

        self.assertEqual(self.sink.device_name, 'other device')
        self.assertEqual(self.sink.rate, 100)
        self.assertEqual(self.sink.channels, 6)
        self.assertEqual(self.sink.periodsize, 0.43)

    def test_acquire_device(self):
        device = mock.Mock()
        self.alsaaudio.PCM.return_value = device

        dir(self.alsaaudio.PCM)
        self.sink.test()
        self.sink.acquire()

        # The ``device`` kwarg was added in pyalsaaudio 0.8
        self.alsaaudio.PCM.assert_called_with(
            mode=self.alsaaudio.PCM_NONBLOCK, device='default')

        device.setformat.assert_called_with(mock.ANY)
        device.setrate.assert_called_with(sc_console.alsa_sink.RATE)
        device.setchannels.assert_called_with(sc_console.alsa_sink.CHANNELS)
        device.setperiodsize.assert_called_with(sc_console.alsa_sink.PERIODSIZE)
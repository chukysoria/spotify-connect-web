import unittest

from tests import mock

import sc_console.alsa_sink
from sc_console.alsa_sink import AlsaSink
import spotifyconnect


class TestAlsaSink(unittest.TestCase):

    @mock.patch('spotifyconnect._session_instance.player.num_listeners')
    def test_defaults(self, listeners):
        listeners.return_value = 0

        sink = AlsaSink('device default')

        self.assertEqual(sink.device_name, 'device default')
        self.assertEqual(sink.rate, sc_console.snapcast_sink.RATE)
        self.assertEqual(sink.channels, sc_console.snapcast_sink.CHANNELS)
        self.assertEqual(sink.periodsize, sc_console.snapcast_sink.PERIODSIZE)
        self.assertEqual(sink.buffer_length, sc_console.snapcast_sink.MAXPERIODS)
        listeners.assert_called_once_with(spotifyconnect.PlayerEvent.MUSIC_DELIVERY)
 
    def test_initialization(self):
        
        sink = AlsaSink('device default', 100, 6, 0.43, 1348)

        self.assertEqual(sink.device_name, 'device default')
        self.assertEqual(sink.rate, 100)
        self.assertEqual(sink.channels, 6)
        self.assertEqual(sink.periodsize, 0.43)
        self.assertEqual(sink.buffer_length, 1348)
import unittest

from tests import mock

import spotifyconnect
import sc_console.snapcast_sink


class TestSnapcastSink(unittest.TestCase):

    def setUp(self):
        self.session = mock.Mock()
        self.session.player.num_listeners.return_value = 0
        spotifyconnect._session_instance = self.session
       
        self.sink = sc_console.snapcast_sink.SnapcastSink()

    def tearDown(self):
        spotifyconnect._session_instance = None

    def test_defaults(self):
        self.assertEqual(self.sink.pipe, None)
        self.assertEqual(self.sink.namedpipe, sc_console.snapcast_sink.NAMEDPIPE)
        
    def test_initialization(self):        
        self.sink = sc_console.snapcast_sink.SnapcastSink('/false/pipe', 5000)

        self.assertEqual(self.sink.namedpipe, '/false/pipe')
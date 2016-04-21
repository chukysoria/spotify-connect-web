import unittest

from tests import mock

import sc_console

from sc_console.connect import PlaybackSession

import spotifyconnect


class Test_Connect(unittest.TestCase):
    
    def test_spotify_key_missing(self):
        
        with self.assertRaises(IOError):
            sc_console.Connect()

class Test_PlaybackSession(unittest.TestCase):

    def test_default(self):

        playback_session = PlaybackSession()

        self.assertFalse(playback_session.active)

    def test_activate(self):

        playback_session = PlaybackSession()
        playback_session.activate()

        self.assertTrue(playback_session.active)


    def test_deactivate(self):

        playback_session = PlaybackSession()
        playback_session.activate()
        playback_session.deactivate()

        self.assertFalse(playback_session.active)
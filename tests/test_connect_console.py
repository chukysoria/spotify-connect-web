import unittest

from tests import mock

import sc_console

from sc_console.connect import PlaybackSession
from sc_console.player_exceptions import PlayerError

import spotifyconnect


class Test_Connect(unittest.TestCase):
    

    @mock.patch('sc_console.connect.alsa_sink')
    @mock.patch('sc_console.connect.spotifyconnect', spec=spotifyconnect)
    def setUp(self, libspotify, mock_alsa):
        self.libspotify = libspotify
        self.mock_alsa = mock_alsa
        self.config = mock.Mock(spec=spotifyconnect.Config)
        self.libspotify.Config.return_value = self.config
        self.session = mock.Mock(spec=spotifyconnect.Session)
        self.libspotify.Session.return_value = self.session
        self.session.player.num_listeners.return_value = 0
        spotifyconnect._session_instance = self.session
        self.sink = mock.Mock(spec= sc_console.alsa_sink.AlsaSink)
        self.mock_alsa.AlsaSink.return_value = self.sink

        self.connect = sc_console.Connect()
    
    def tearDown(self):
        spotifyconnect._session_instance = None    
    
    def test_spotify_key_missing(self):
        
        with self.assertRaises(IOError):
            sc_console.Connect()
    
    def test_init_defaults(self):
        self.libspotify.Config.assert_called_once_with()
        self.assertEqual(self.config.remote_name, 'TestConnect')
        connection_calls = [mock.call(self.libspotify.ConnectionEvent.CONNECTION_NOTIFY_UPDATED, self.connect.connection_notify),
                 mock.call(self.libspotify.ConnectionEvent.NEW_CREDENTIALS, self.connect.connection_new_credentials)] 
        self.session.connection.on.assert_has_calls(connection_calls, any_order = True)
        player_calls = [mock.call(self.libspotify.PlayerEvent.PLAYBACK_NOTIFY, self.connect.playback_notify),
                 mock.call(self.libspotify.PlayerEvent.PLAYBACK_SEEK, self.connect.playback_seek)] 
        self.session.player.on.assert_has_calls(player_calls, any_order = True)
        self.mock_alsa.AlsaSink.assert_called_once_with('default')


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
import unittest
import os
import pytest

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
        self.event_loop = mock.Mock(spec = spotifyconnect.EventLoop)
        self.libspotify.EventLoop.return_value = self.event_loop
        open_mock = mock.mock_open(read_data='{}')
        with mock.patch('sc_console.connect.open', open_mock, create=True) as self.opencredentials:
            self.connect = sc_console.Connect()
    
    def tearDown(self):
        spotifyconnect._session_instance = None    
    
    def test_spotify_key_missing(self):
        
        with self.assertRaises(IOError):
            sc_console.Connect()
    
    def test_init_defaults(self):
        self.opencredentials.assert_called_once_with('credentials.json')        
        self.libspotify.Config.assert_called_once_with()
        key_path = os.path.join(
                os.path.dirname(
                    os.path.realpath(sc_console.connect.__file__)), 'spotify_appkey.key')
        self.config.load_application_key_file.assert_called_once_with(key_path)
        self.assertEqual(self.config.remote_name, 'TestConnect')
        connection_calls = [mock.call(self.libspotify.ConnectionEvent.CONNECTION_NOTIFY_UPDATED, self.connect.connection_notify),
                 mock.call(self.libspotify.ConnectionEvent.NEW_CREDENTIALS, self.connect.connection_new_credentials)] 
        self.session.connection.on.assert_has_calls(connection_calls, any_order = True)
        player_calls = [mock.call(self.libspotify.PlayerEvent.PLAYBACK_NOTIFY, self.connect.playback_notify),
                 mock.call(self.libspotify.PlayerEvent.PLAYBACK_SEEK, self.connect.playback_seek),
                 mock.call(self.libspotify.PlayerEvent.PLAYBACK_VOLUME, self.connect.volume_set)] 
        self.session.player.on.assert_has_calls(player_calls, any_order = True)
        self.mock_alsa.AlsaSink.assert_called_once_with('default')
        self.sink.mixer_load.assert_called_once_with('', volmin=0, volmax=100)
        self.assertEqual(self.connect.audio_player, self.sink)
        self.session.player.set_bitrate.assert_called_once_with(self.libspotify.Bitrate.BITRATE_160k)
        self.libspotify.EventLoop.assert_called_once_with(self.session)
        self.event_loop.start.assert_called_once_with()

    @mock.patch('sc_console.connect.alsa_sink')
    @mock.patch('sc_console.connect.spotifyconnect', spec=spotifyconnect)
    def test_arguments(self, libspotify, mock_alsa):
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
        self.event_loop = mock.Mock(spec = spotifyconnect.EventLoop)
        self.libspotify.EventLoop.return_value = self.event_loop

        parser = self.connect._createparser()
        args = parser.parse_args(['-d', 
                                  '-k', '/route/to/key',
                                  '-u', 'foo',
                                  '-p', 'bar',
                                  '-n', 'player',
                                  '-b', '320',
                                  '-a', 'alsa',
                                  '-D', 'newdevice',
                                  '-m', 'LineIn',
                                  '-v', '20',
                                  '-V', '80'])
        self.connect._main(args)

        # Debug
        connection_calls = [mock.call(self.libspotify.DebugEvent.DEBUG_MESSAGE, self.connect.debug_message)] 
        self.session.connection.on.assert_has_calls(connection_calls, any_order = True)
        # Key path
        self.config.load_application_key_file.assert_called_once_with('/route/to/key')
        # Username
        self.connect.credentials['username'] = 'foo'
        # Password
        self.session.connection.login.assert_called_once_with('foo', password = 'bar')
        # Name
        self.config.remote_name = 'player'
        # Bitrate
        self.session.player.set_bitrate.asser_called_once_with(self.libspotify.Bitrate.BITRATE_320k)
        # Alsa device
        self.mock_alsa.AlsaSink.assert_called_once_with('newdevice')
        #Mixer
        self.sink.mixer_load.assert_called_once_with('LineIn', volmin=20, volmax=80)

    @mock.patch('sc_console.connect.snapcast_sink')
    @mock.patch('sc_console.connect.spotifyconnect', spec=spotifyconnect)
    def test_arguments_2(self, libspotify, mock_snapcast):
        self.libspotify = libspotify
        self.mock_snapcast = mock_snapcast
        self.config = mock.Mock(spec=spotifyconnect.Config)
        self.libspotify.Config.return_value = self.config
        self.session = mock.Mock(spec=spotifyconnect.Session)
        self.libspotify.Session.return_value = self.session
        self.session.player.num_listeners.return_value = 0
        spotifyconnect._session_instance = self.session
        self.sink = mock.Mock(spec= sc_console.snapcast_sink.SnapcastSink)
        self.mock_snapcast.SnapcastSink.return_value = self.sink
        self.event_loop = mock.Mock(spec = spotifyconnect.EventLoop)
        self.libspotify.EventLoop.return_value = self.event_loop
        open_mock = mock.mock_open(read_data='{"username": "foo", "device-id": "9999", "blob": "longblob"}')
        parser = self.connect._createparser()
        args = parser.parse_args(['-b', '90',
                                  '-c', '/fake/path',
                                  '-a', 'snapcast'])

        with mock.patch('sc_console.connect.open', open_mock, create=True) as m:
            self.connect._main(args)

        # Bitrate
        self.session.player.set_bitrate.asser_called_once_with(self.libspotify.Bitrate.BITRATE_90k)
        # Snapcast device
        self.mock_snapcast.SnapcastSink.assert_called_once_with()
        # Custom credentials file
        m.assert_called_once_with('/fake/path')
        self.session.connection.login.assert_called_once_with('foo', blob = 'longblob')
        self.config.device_id = '9999'

    def test_connection_notify(self):
        self.connect.connection_notify(spotifyconnect.ConnectionState.LoggedIn, self.session)
        resout, reserr = self.capfd.readouterr()
        self.assertEqual(resout, 'LoggedIn')


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
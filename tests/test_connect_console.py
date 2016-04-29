import os
import pytest

from tests import mock

import sc_console

from sc_console.connect import PlaybackSession
from sc_console.player_exceptions import PlayerError

import spotifyconnect

def test_init_defaults(libspotify, alsasink_module, mock_alsasink, connect, sp_eventloop, openfile):
    openfile.assert_called_once_with('credentials.json')
    libspotify.Config.assert_called_once_with()
    key_path = os.path.join(
            os.path.dirname(
                os.path.realpath(sc_console.connect.__file__)), 'spotify_appkey.key')
    connect.config.load_application_key_file.assert_called_once_with(key_path)
    assert connect.config.remote_name == 'TestConnect'
    libspotify.Session.assert_called_once_with(connect.config)
    connection_calls = [mock.call(libspotify.ConnectionEvent.CONNECTION_NOTIFY_UPDATED, connect.connection_notify),
                mock.call(libspotify.ConnectionEvent.NEW_CREDENTIALS, connect.connection_new_credentials)] 
    connect.session.connection.on.assert_has_calls(connection_calls, any_order = True)
    player_calls = [mock.call(libspotify.PlayerEvent.PLAYBACK_NOTIFY, connect.playback_notify),
                mock.call(libspotify.PlayerEvent.PLAYBACK_SEEK, connect.playback_seek),
                mock.call(libspotify.PlayerEvent.PLAYBACK_VOLUME, connect.volume_set)] 
    connect.session.player.on.assert_has_calls(player_calls, any_order = True)
    alsasink_module.AlsaSink.assert_called_once_with('default')
    assert connect.audio_player == mock_alsasink
    connect.audio_player.mixer_load.assert_called_once_with('', volmin=0, volmax=100)
    connect.session.player.set_bitrate.assert_called_once_with(libspotify.Bitrate.BITRATE_160k)
    libspotify.EventLoop.assert_called_once_with(connect.session)
    sp_eventloop.start.assert_called_once_with()

@pytest.mark.commandline(['-d', 
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
def test_arguments(connect, libspotify, alsasink_module, libalsa):
    # Debug
    connection_calls = [mock.call(libspotify.DebugEvent.DEBUG_MESSAGE, connect.debug_message)] 
    connect.session.connection.on.assert_has_calls(connection_calls, any_order = True)
    # Key path
    connect.config.load_application_key_file.assert_called_once_with('/route/to/key')
    # Username
    assert connect.credentials['username'] == 'foo'
    # Password
    connect.session.connection.login.assert_called_once_with('foo', password = 'bar')
    # Name
    assert connect.config.remote_name == 'player'
    # Bitrate
    connect.session.player.set_bitrate.asser_called_once_with(libspotify.Bitrate.BITRATE_320k)
    # Alsa device
    alsasink_module.AlsaSink.assert_called_once_with('newdevice')
    #Mixer
    connect.audio_player.mixer_load.assert_called_once_with('LineIn', volmin=20, volmax=80)

@pytest.mark.credentials_file('{"username": "foo", "device-id": "9999", "blob": "longblob"}')
@pytest.mark.commandline(['-b', '90',
                          '-c', '/fake/path',
                          '-a', 'snapcast'])
def test_arguments_2(connect, snapsink, openfile, libspotify):
    # Bitrate
    connect.session.player.set_bitrate.asser_called_once_with(libspotify.Bitrate.BITRATE_90k)
    # Snapcast device
    connect.audio_player = snapsink
    # Custom credentials file
    openfile.assert_called_once_with('/fake/path')
    connect.session.connection.login.assert_called_once_with('foo', blob = 'longblob')
    connect.session.config.device_id = '9999'

def test_spotify_key_missing():
    
    with pytest.raises(IOError):
        sc_console.Connect()

def test_connection_notify(connect, capsys):
    connect.connection_notify(spotifyconnect.ConnectionState.LoggedIn, connect.session)
    out, err = capsys.readouterr()
    assert out == 'LoggedIn\n'

@pytest.mark.commandline(['-d'])
def test_debug_message(connect, capsys):
    connect.debug_message('foo', connect.session)
    out, err = capsys.readouterr()
    assert out == 'foo\n'

def test_volume_set(connect, capsys):
    connect.volume_set(47, connect.session)
    out, err = capsys.readouterr()
    assert out == 'volume: 47\n'
    assert connect.audio_player.volume_set(47)

def test_playback_seek(connect, capsys):
    connect.playback_seek(875, connect.session)
    out, err = capsys.readouterr()
    assert out =="playback_seek: 875\n"

# Playback sessions
def test_playback_session_default():
    playback_session = PlaybackSession()

    assert not playback_session.active

def test_playback_session_activate():
    playback_session = PlaybackSession()
    playback_session.activate()

    assert playback_session.active


def test_playback_session_deactivate():
    playback_session = PlaybackSession()
    playback_session.activate()
    playback_session.deactivate()

    assert not playback_session.active
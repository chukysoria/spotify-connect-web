import os

import pytest

from spotifyconnect import PlaybackNotify

import sc_console
from sc_console.connect import PlaybackSession

from tests import mock


def test_init_defaults(
        libspotify,
        alsasink_class,
        mock_alsasink,
        connect,
        sp_eventloop,
        openfile):
    openfile.assert_called_once_with('credentials.json')
    libspotify.Config.assert_called_once_with()
    key_path = os.path.join(
        os.path.dirname(
            os.path.realpath(
                sc_console.connect.__file__)),
        'spotify_appkey.key')
    connect.config.load_application_key_file.assert_called_once_with(key_path)
    assert connect.config.remote_name == 'TestConnect'
    libspotify.Session.assert_called_once_with(connect.config)
    connection_calls = [
        mock.call(
            libspotify.ConnectionEvent.CONNECTION_NOTIFY_UPDATED,
            connect.connection_notify),
        mock.call(
            libspotify.ConnectionEvent.NEW_CREDENTIALS,
            connect.connection_new_credentials)]
    connect.session.connection.on.assert_has_calls(
        connection_calls, any_order=True)
    player_calls = [
        mock.call(
            libspotify.PlayerEvent.PLAYBACK_NOTIFY,
            connect.playback_notify),
        mock.call(
            libspotify.PlayerEvent.PLAYBACK_SEEK,
            connect.playback_seek),
        mock.call(
                libspotify.PlayerEvent.PLAYBACK_VOLUME, connect.volume_set)]
    connect.session.player.on.assert_has_calls(player_calls, any_order=True)
    alsasink_class.assert_called_once_with('default')
    assert connect.audio_player == mock_alsasink
    connect.audio_player.mixer_load.assert_called_once_with(
        '', volmin=0, volmax=100)
    connect.session.player.set_bitrate.assert_called_once_with(
        libspotify.Bitrate.BITRATE_160k)
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
def test_arguments(connect, libspotify, alsasink_class, libalsa):
    # Debug
    connection_calls = [
        mock.call(
            libspotify.DebugEvent.DEBUG_MESSAGE,
            connect.debug_message)]
    connect.session.connection.on.assert_has_calls(
        connection_calls, any_order=True)
    # Key path
    connect.config.load_application_key_file.assert_called_once_with(
        '/route/to/key')
    # Username
    assert connect._credentials['username'] == 'foo'
    # Password
    connect.session.connection.login.assert_called_once_with(
        'foo', password='bar')
    # Name
    assert connect.config.remote_name == 'player'
    # Bitrate
    connect.session.player.set_bitrate.asser_called_once_with(
        libspotify.Bitrate.BITRATE_320k)
    # Alsa device
    alsasink_class.assert_called_once_with('newdevice')
    # Mixer
    connect.audio_player.mixer_load.assert_called_once_with(
        'LineIn', volmin=20, volmax=80)


@pytest.mark.credentials_file(
    '{"username": "foo", "device-id": "9999", "blob": "longblob"}')
@pytest.mark.commandline(['-b', '90',
                          '-c', '/fake/path',
                          '-a', 'snapcast'])
def test_arguments_2(connect, snapsink, openfile, libspotify):
    # Bitrate
    connect.session.player.set_bitrate.asser_called_once_with(
        libspotify.Bitrate.BITRATE_90k)
    # Snapcast device
    connect.audio_player = snapsink
    # Custom credentials file
    openfile.assert_called_once_with('/fake/path')
    connect.session.connection.login.assert_called_once_with(
        b'foo', blob=b'longblob')
    connect.session.config.device_id = '9999'


def test_spotify_key_missing():

    with pytest.raises(IOError):
        sc_console.Connect()


def test_connection_new_credentials(connect, capsys):
    connect.connection_new_credentials('longblob', connect.session)
    out, err = capsys.readouterr()
    assert out == 'longblob\n'
    assert connect._credentials['blob'] == 'longblob'
    assert connect._credentials['username'] == 'active user'


@pytest.mark.commandline(['-d'])
def test_debug_message(connect, capsys):
    connect.debug_message('foo', connect.session)
    out, err = capsys.readouterr()
    assert out == 'foo\n'


@pytest.mark.parametrize('notify, expected', [
    (PlaybackNotify.Play, 'kSpPlaybackNotifyPlay'),
    (PlaybackNotify.TrackChanged, 'kSpPlaybackNotifyTrackChanged'),
    (PlaybackNotify.Next, "kSpPlaybackNotifyNext"),
    (PlaybackNotify.Prev, "kSpPlaybackNotifyPrev"),
    (PlaybackNotify.ShuffleEnabled, "kSpPlaybackNotifyShuffleEnabled"),
    (PlaybackNotify.ShuffleDisabled, "kSpPlaybackNotifyShuffleDisabled"),
    (PlaybackNotify.RepeatEnabled, "kSpPlaybackNotifyRepeatEnabled"),
    (PlaybackNotify.RepeatDisabled, "kSpPlaybackNotifyRepeatDisabled"),
    (PlaybackNotify.BecameActive, "kSpPlaybackNotifyBecameActive"),
    (PlaybackNotify.PlayTokenLost, "kSpPlaybackNotifyPlayTokenLost"),
    (PlaybackNotify.AudioFlush, "kSpPlaybackEventAudioFlush"),
    (19, "UNKNOWN PlaybackNotify 19")])
def test_playback_notify(connect, capsys, notify, expected):
    connect.playback_notify(notify, connect.session)
    out, err = capsys.readouterr()
    assert out == (expected + '\n')


def test_playback_notify_BecameInactive(connect, capsys):
    connect.playback_notify(
        PlaybackNotify.BecameActive,
        connect.session)
    assert connect.playback_session.active


@pytest.mark.parametrize('notify, expected', [
    (PlaybackNotify.Pause, 'kSpPlaybackNotifyPause'),
    (PlaybackNotify.BecameInactive, 'kSpPlaybackNotifyBecameInactive')])
@pytest.mark.parametrize('acquired', [
    True,
    False])
def test_playback_notify_release(
        connect,
        capsys,
        mock_alsasink,
        acquired,
        notify,
        expected):
    mock_alsasink.acquired.return_value = acquired
    connect.playback_notify(notify, connect.session)
    out, err = capsys.readouterr()
    expected += "\n"
    if acquired:
        connect.audio_player.pause.assert_called_once_with()
        connect.audio_player.release.assert_called_once_with()
        expected += "DeviceReleased\n"
    else:
        connect.audio_player.pause.assert_not_called
        connect.audio_player.release.assert_not_called
    assert out == expected


@pytest.mark.parametrize('acquired', [
    True,
    False])
def test_playback_notify_AudioFlush(connect, capsys, mock_alsasink, acquired):
    mock_alsasink.acquired.return_value = acquired
    connect.playback_notify(
        PlaybackNotify.AudioFlush,
        connect.session)
    out, err = capsys.readouterr()
    if acquired:
        connect.audio_player.buffer_flush.assert_called_once_with()
    else:
        connect.audio_player.buffer_flush.assert_not_called
    assert out == "kSpPlaybackEventAudioFlush\n"


def test_volume_set(connect, capsys):
    connect.volume_set(47, connect.session)
    out, err = capsys.readouterr()
    assert out == 'volume: 47\n'
    assert connect.audio_player.volume_set(47)


def test_playback_seek(connect, capsys):
    connect.playback_seek(875, connect.session)
    out, err = capsys.readouterr()
    assert out == "playback_seek: 875\n"


def test_zeroconf_vars(connect, capsys, sp_zeroconf):
    connect.print_zeroconf_vars(sp_zeroconf)
    out, err = capsys.readouterr()
    assert out == ("public key: public key\n"
                   "device id: device id\n"
                   "remote name: remote name\n"
                   "account req: premium\n"
                   "device type: device type\n")

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

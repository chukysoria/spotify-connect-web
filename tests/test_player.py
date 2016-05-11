from threading import Event

import pytest

from six.moves import range

import spotifyconnect

from scweb.player import BufferFull
from tests import mock


def test_defaults(player):
    assert player._device is None
    assert player._mixer is None


def test_music_delivery_writes_frames_to_stream(player, sp_session):
    player.write = mock.Mock()
    player.buffer_length = mock.Mock(return_value=1)
    audio_format = mock.Mock()
    samples = [0]
    samples = 'a' * 4412
    num_samples = 2206
    pending = spotifyconnect.ffi.new('int *')

    num_consumed_samples = player._on_music_delivery(
        audio_format, samples, num_samples, pending, sp_session)

    assert num_consumed_samples == num_samples
    assert pending[0] == 2205
    player.write.assert_called_once_with('a' * 4410)


def test_music_delivery_writes_frames_to_stream_full(player, sp_session):
    player.write = mock.Mock(side_effect=BufferFull)
    player.buffer_length = mock.Mock(return_value=0)
    audio_format = mock.Mock()
    samples = [0]
    samples = 'a' * 4412
    num_samples = 2206
    pending = spotifyconnect.ffi.new('int *')

    num_consumed_samples = player._on_music_delivery(
        audio_format, samples, num_samples, pending, sp_session)

    assert num_consumed_samples == 0
    assert pending[0] == 0
    player.write.assert_called_once_with('a' * 4410)


@pytest.mark.parametrize("mixer, expected", [
    (mock.Mock(), True),
    (None, False)
])
def test_mixer_loaded(player, mixer, expected):
    player._mixer = mixer
    assert player.mixer_loaded() == expected


@pytest.mark.parametrize("dev, expected", [
    (mock.Mock(), True),
    (None, False)
])
def test_acquired_device(player, dev, expected):
    player._device = dev

    assert player.acquired() == expected


def test_off_closes_audio_device(player):
    player.off()

    player.release.assert_called_with()


def test_playback_thread(player):
    e = Event()
    player.queue.put('a', block=False)
    with pytest.raises(NotImplementedError):
        player.playback_thread(player.queue, e)


def test_play(player):
    player.play()

    assert player.t.daemon
    assert player.t.isAlive()


def test_pause(player):
    player.play()
    player.pause()

    assert not player.t.isAlive()


@pytest.mark.parametrize("expected", [
    True,
    False
])
def test_playing(player, expected):
    player.t.isAlive = mock.Mock(return_value=expected)

    assert player.playing() == expected


def test_write(player):
    player.write('abcd')
    data = player.queue.get()

    assert data == 'abcd'


def test_write_full(player):
    with pytest.raises(BufferFull):
        for i in range(51):
            player.write(i)


def test_buffer_flush(player):
    player.queue.put('a', block=False)
    player.buffer_flush()

    player.queue.qsize() == 0


def test_buffer_length(player):
    player.queue.put('a', block=False)

    player.buffer_length() == 1


def test_volrange_set(player):
    player.volrange_set(10, 76)

    assert player.volmin == 10
    assert player.volmax == 76


@pytest.mark.parametrize("device_volume, volmin, volmax, expected", [
    (74, 0, 100, 74),
    (74, 0, 70, 100),
    (35, 0, 70, 50),
    (10, 20, 100, 0),
    (40, 20, 100, 25),
    (60, 20, 80, 67)
])
def test_volume_get_standard(player, device_volume, volmin, volmax, expected):
    player._getvolume.return_value = device_volume
    player.volmin = volmin
    player.volmax = volmax

    result = player.volume_get()

    assert result == expected


@pytest.mark.parametrize("volume, volmin, volmax, expected", [
    (74, 0, 100, 74),
    (0, 0, 100, 0),
    (100, 0, 70, 70),
    (50, 0, 70, 35),
    (25, 20, 100, 40),
    (67, 20, 80, 60),
    (0, 20, 80, 20)
])
def test_volume_set(player, volume, volmin, volmax, expected):
    player._getmute.return_value = True
    player.volmin = volmin
    player.volmax = volmax
    player.volume_set(volume)

    player._setvolume.assert_called_once_with(expected)
    if volume == 0:
        player._setmute.assert_called_once_with(True)
    else:
        player._setmute.assert_called_once_with(False)

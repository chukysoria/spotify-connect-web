import pytest

import spotifyconnect

from tests import mock


def test_defaults(player):
    assert player.t.name == 'PlayerLoop'
    assert player._device is None
    assert player._mixer is None


def test_music_delivery_writes_frames_to_stream(player):
    player._device = mock.Mock()
    player.write = mock.Mock()
    audio_format = mock.Mock()
    audio_format.sample_type = spotifyconnect.SampleType.S16NativeEndian
    pending = [0]
    frames = 'abcd'

    num_consumed_frames = player._on_music_delivery(
        audio_format, frames,
        mock.sentinel.num_samples, pending, mock.sentinel.session)

    assert num_consumed_frames == mock.sentinel.num_samples


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


@pytest.mark.parametrize("expected", [
    True,
    False
])
def test_playing(player, expected):
    player.t.isAlive = mock.Mock(return_value=expected)

    assert player.playing() == expected


def test_volrange_set(alsasink):
    alsasink.volrange_set(10, 76)

    assert alsasink.volmin == 10
    assert alsasink.volmax == 76


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

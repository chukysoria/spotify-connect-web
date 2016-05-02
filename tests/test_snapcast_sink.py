import pytest

import spotifyconnect

import sc_console.snapcast_sink

from tests import mock


def test_defaults(snapsink):
    assert snapsink._device is None
    assert snapsink.namedpipe == sc_console.snapcast_sink.NAMEDPIPE


def test_initialization(sp_session):
    snapsink = sc_console.snapcast_sink.SnapcastSink('/false/pipe', 5000)

    assert snapsink.namedpipe == '/false/pipe'


def test_off_closes_audio_device(snapsink, snapcast_os):
    pipe = mock.sentinel.pipe
    snapsink._device = pipe

    snapsink.off()

    snapcast_os.close.assert_called_with(pipe)
    assert snapsink._device is None


def test_acquire_device(snapsink, snapcast_os):
    snapsink.namedpipe = 'named_pipe'
    snapcast_os.open.return_value = mock.sentinel.pipe

    snapsink.acquire()

    snapcast_os.open.assert_called_with('named_pipe', snapcast_os.O_WRONLY)
    assert snapsink._device == mock.sentinel.pipe

def test_acquire_device_raises_error(snapsink, snapcast_os):
    snapcast_os.open.side_effect = IOError('error')

    with pytest.raises(sc_console.player.PlayerError):
        snapsink.acquire()

def test_aquired_device_property_true(snapsink):
    snapsink._device = mock.Mock()

    assert snapsink.acquired()


def test_aquired_device_property_false(snapsink):
    snapsink._device = None

    assert not snapsink.acquired()


def test_music_delivery_writes_frames_to_stream(snapsink):
    snapsink._device = mock.Mock()
    snapsink.write = mock.Mock()
    audio_format = mock.Mock()
    audio_format.sample_type = spotifyconnect.SampleType.S16NativeEndian
    pending = [0]
    frames = "abcd"

    num_consumed_frames = snapsink._on_music_delivery(
        audio_format, frames,
        mock.sentinel.num_samples, pending, mock.sentinel.session)

    assert num_consumed_frames == mock.sentinel.num_samples

def test_writedata(snapsink, snapcast_os):
    mock_pipe = mock.Mock()
    snapsink._device = mock_pipe
    snapsink._writedata('abcd')
    snapcast_os.write.assert_called_once_with(mock_pipe, 'abcd')

def test_mixer_load(snapsink):
    snapsink.mixer_load()
    assert snapsink.volmin == 0
    assert snapsink.volmax == 100

def test_mixer_unload(snapsink):
    snapsink.mixer_unload()

    assert snapsink._mixer is None

def test_getvolume(snapsink):
    result = snapsink._getvolume()

    assert result == 100

def test_setvolume(snapsink):
    snapsink._setvolume(10)

def test_playing_true(snapsink):
    snapsink.t.isAlive = mock.Mock(return_value=True)

    assert snapsink.playing()


def test_playing_false(snapsink):
    snapsink.t.isAlive = mock.Mock(return_value=False)

    assert not snapsink.playing()

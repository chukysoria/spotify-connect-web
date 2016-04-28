import unittest

from tests import mock

import spotifyconnect
import sc_console.snapcast_sink


def test_defaults(snapsink):
    assert snapsink._pipe == None
    assert snapsink.namedpipe == sc_console.snapcast_sink.NAMEDPIPE
        
def test_initialization(sp_session):        
    snapsink = sc_console.snapcast_sink.SnapcastSink('/false/pipe', 5000)

    assert snapsink.namedpipe == '/false/pipe'

def test_off_closes_audio_device(snapsink, snapcast_os):
    pipe = mock.sentinel.pipe
    snapsink._pipe = pipe
        
    snapsink.off()

    snapcast_os.close.assert_called_with(pipe)
    assert snapsink._pipe is None

def test_acquire_device(snapsink, snapcast_os):
    snapsink.namedpipe = 'named_pipe'
    snapcast_os.open.return_value = mock.sentinel.pipe

    snapsink.acquire()

    # The ``device`` kwarg was added in pyalsaaudio 0.8
    snapcast_os.open.assert_called_with('named_pipe', snapcast_os.O_WRONLY)
    assert snapsink._pipe == mock.sentinel.pipe

def test_aquired_device_property_true(snapsink):
    snapsink._pipe = mock.Mock()

    assert snapsink.acquired()

def test_aquired_device_property_false(snapsink):
    snapsink._pipe = None

    assert not snapsink.acquired()

def test_music_delivery_writes_frames_to_stream(snapsink):
    snapsink._pipe = mock.Mock()
    snapsink.write = mock.Mock()
    audio_format = mock.Mock()
    audio_format.sample_type = spotifyconnect.SampleType.S16NativeEndian
    pending = [0]
    frames = "a" * 10000

    num_consumed_frames = snapsink._on_music_delivery(
        audio_format, 'abcd',
            mock.sentinel.num_samples, pending, mock.sentinel.session)

    assert num_consumed_frames == mock.sentinel.num_samples

def test_playing_true(snapsink):
    snapsink.t.isAlive = mock.Mock(return_value=True)

    assert snapsink.playing()

def test_playing_true(snapsink):
    snapsink.t.isAlive = mock.Mock(return_value=False)

    assert not snapsink.playing()
import alsaaudio

import pytest

import spotifyconnect

import sc_console.player
import sc_console.alsa_sink

from tests import mock


def test_off_closes_audio_device(alsasink):
    device_mock = mock.Mock()
    alsasink._device = device_mock

    alsasink.off()

    device_mock.close.assert_called_with()
    assert alsasink._device is None


def test_defaults(alsasink, sp_session):
    assert alsasink.device_name == 'default'
    assert alsasink.rate == sc_console.alsa_sink.RATE
    assert alsasink.channels == sc_console.alsa_sink.CHANNELS
    assert alsasink.periodsize == sc_console.alsa_sink.PERIODSIZE
    sp_session.player.num_listeners.assert_called_once_with(
        spotifyconnect.PlayerEvent.MUSIC_DELIVERY)


def test_initialization(alsasink):
    alsasink = sc_console.alsa_sink.AlsaSink(
        'other device', 100, 6, 0.43, 1348)

    assert alsasink.device_name == 'other device'
    assert alsasink.rate == 100
    assert alsasink.channels == 6
    assert alsasink.periodsize == 0.43


def test_acquire_device(alsasink, libalsa, device):
    alsasink.acquire()

    # The ``device`` kwarg was added in pyalsaaudio 0.8
    libalsa.PCM.assert_called_with(libalsa.PCM_PLAYBACK, device='default')
    device.setrate.assert_called_with(sc_console.alsa_sink.RATE)
    device.setchannels.assert_called_with(sc_console.alsa_sink.CHANNELS)
    device.setperiodsize.assert_called_with(sc_console.alsa_sink.PERIODSIZE)

def test_acquire_device_raise_error(alsasink, libalsa):
    libalsa.PCM.side_effect = alsaaudio.ALSAAudioError('error')
    with pytest.raises(sc_console.player.PlayerError):
        alsasink.acquire()

def test_music_delivery_creates_device_with_alsaaudio_0_7(alsasink, libalsa):
    del libalsa.pcms  # Remove pyalsaudio 0.8 version marker

    alsasink.acquire()

    # The ``card`` kwarg was deprecated in pyalsaaudio 0.8
    libalsa.PCM.assert_called_with(libalsa.PCM_PLAYBACK, card='default')


@pytest.mark.parametrize("dev, expected", [
    (mock.Mock(), True),
    (None, False)
])
def test_acquired_device(alsasink, dev, expected):
    alsasink._device = dev

    assert alsasink.acquired() == expected

def test_writedata_to_device(alsasink):
    device_mock = mock.Mock()
    alsasink._device = device_mock
    alsasink._writedata('abcd')
    device_mock.write.assert_called_once_with('abcd')

@pytest.mark.parametrize("format,expected", [
    ('little', alsaaudio.PCM_FORMAT_S16_LE),
    ("big", alsaaudio.PCM_FORMAT_S16_BE)
])
def test_sets_endian_format(alsasink, libalsa, device, format, expected):
    with mock.patch('sc_console.alsa_sink.sys') as sys_mock:
        sys_mock.byteorder = format

        alsasink.acquire()

    device.setformat.assert_called_with(expected)


def test_music_delivery_writes_frames_to_stream(alsasink):
    alsasink._device = mock.Mock()
    alsasink.write = mock.Mock()
    audio_format = mock.Mock()
    audio_format.sample_type = spotifyconnect.SampleType.S16NativeEndian
    pending = [0]
    frames = 'abcd'

    num_consumed_frames = alsasink._on_music_delivery(
        audio_format, frames,
        mock.sentinel.num_samples, pending, mock.sentinel.session)

    assert num_consumed_frames == mock.sentinel.num_samples


@pytest.mark.parametrize('pcms_name, device_name, cardindex', [
    ('default', 'default', -1),
    ('default:dev=surround', 'surround', -1),
    ('default:CARD=card1', 'default', 1),
    ('default:CARD=card1,DEV=surround', 'surround', 1),
    ('default:CARD=card0', 'default', 0)
])
@pytest.mark.parametrize("mix_args, mixer_name, volmin, volmax", [
    ({}, 'PCM', 0, 100),
    ({'volmin': 20}, 'PCM', 20, 100),
    ({'volmax': 80}, 'PCM', 0, 80),
    ({'volmin': 20, 'volmax': 80}, 'PCM', 20, 80),
    ({'mixer': 'LineIn'}, 'LineIn', 0, 100)
])
def test_mixer_load(
        alsasink,
        libalsa,
        mixer,
        mix_args,
        mixer_name,
        volmin,
        volmax,
        pcms_name,
        device_name,
        cardindex):
    alsasink.device_name = pcms_name
    alsasink.mixer_load(**mix_args)

    if 'mixer' not in mix_args:
        libalsa.mixers.assert_called_with(
            device=device_name, cardindex=cardindex)
    libalsa.Mixer.assert_called_with(
        mixer_name,
        device=device_name,
        cardindex=cardindex)
    assert alsasink._mixer == mixer
    assert alsasink.volmin == volmin
    assert alsasink.volmax == volmax

def test_mixer_list_raises_errors(alsasink, libalsa):
    libalsa.mixers.side_effect = alsaaudio.ALSAAudioError('error')

    with pytest.raises(sc_console.player.PlayerError):
        alsasink.mixer_load()

def test_mixer_load_raises_if_no_mixers(alsasink, libalsa):
    libalsa.mixers.return_value = []

    with pytest.raises(sc_console.player.PlayerError):
        alsasink.mixer_load()

def test_mixer_load_raises_errors(alsasink, libalsa):
    libalsa.Mixer.side_effect = alsaaudio.ALSAAudioError('error')

    with pytest.raises(sc_console.player.PlayerError):
        alsasink.mixer_load()

def test_mixer_unload(alsasink, mixer):
    alsasink._mixer = mixer
    alsasink.mixer_unload()

    mixer.close.assert_called_once_with()
    alsasink._mixer = None

@pytest.mark.parametrize("mixer, expected", [
    (mock.Mock(), True),
    (None, False)
])
def test_mixer_loaded(alsasink, mixer, expected):
    alsasink._mixer = mixer
    assert alsasink.mixer_loaded() == expected


@pytest.mark.parametrize("expected", [
    True,
    False
])
def test_playing(alsasink, expected):
    alsasink.t.isAlive = mock.Mock(return_value=expected)

    assert alsasink.playing() == expected
        

def test_volrange_set(alsasink):
    alsasink.volrange_set(10, 76)

    assert alsasink.volmin == 10
    assert alsasink.volmax == 76


@pytest.mark.parametrize("alsa_volume, volmin, volmax, expected", [
    (74, 0, 100, 74),
    (74, 0, 70, 100),
    (35, 0, 70, 50),
    (10, 20, 100, 0),
    (40, 20, 100, 25),
    (60, 20, 80, 67)
])
def test_volume_get_standard(alsasink, alsa_volume, volmin, volmax, expected):
    alsasink._mixer.getvolume.return_value = [alsa_volume]
    alsasink.volmin = volmin
    alsasink.volmax = volmax

    result = alsasink.volume_get()

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
def test_volume_set(alsasink, volume, volmin, volmax, expected):
    alsasink._mixer.getmute.return_value = [1]
    alsasink.volmin = volmin
    alsasink.volmax = volmax
    alsasink.volume_set(volume)

    alsasink._mixer.setvolume.assert_called_once_with(expected)
    if volume == 0:
        alsasink._mixer.setmute.assert_called_once_with(1)
    else:
        alsasink._mixer.setmute.assert_called_once_with(0)

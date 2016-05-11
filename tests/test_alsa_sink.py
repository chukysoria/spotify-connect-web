import alsaaudio

import pytest

import spotifyconnect

import scweb.alsa_sink
import scweb.player

from tests import mock


def test_defaults(alsasink, sp_session):
    assert alsasink.device_name == 'default'
    assert alsasink.rate == scweb.alsa_sink.RATE
    assert alsasink.channels == scweb.alsa_sink.CHANNELS
    assert alsasink.periodsize == scweb.alsa_sink.PERIODSIZE
    sp_session.player.num_listeners.assert_called_once_with(
        spotifyconnect.PlayerEvent.MUSIC_DELIVERY)


def test_initialization(alsasink):
    alsasink = scweb.alsa_sink.AlsaSink(
        'other device', 100, 6, 0.43, 1348)

    assert alsasink.device_name == 'other device'
    assert alsasink.rate == 100
    assert alsasink.channels == 6
    assert alsasink.periodsize == 0.43


def test_acquire_device(alsasink, libalsa, device):
    alsasink.acquire()

    # The ``device`` kwarg was added in pyalsaaudio 0.8
    libalsa.PCM.assert_called_with(libalsa.PCM_PLAYBACK, device='default')
    device.setrate.assert_called_with(scweb.alsa_sink.RATE)
    device.setchannels.assert_called_with(scweb.alsa_sink.CHANNELS)
    device.setperiodsize.assert_called_with(scweb.alsa_sink.PERIODSIZE)


def test_acquire_with_alsaaudio_0_7(alsasink, libalsa):
    del libalsa.pcms  # Remove pyalsaudio 0.8 version marker

    alsasink.acquire()

    # The ``card`` kwarg was deprecated in pyalsaaudio 0.8
    libalsa.PCM.assert_called_with(libalsa.PCM_PLAYBACK, card='default')


def test_acquire_device_raise_error(alsasink, libalsa):
    libalsa.PCM.side_effect = alsaaudio.ALSAAudioError('error')
    with pytest.raises(scweb.player.PlayerError):
        alsasink.acquire()


def test_release(alsasink):
    device_mock = mock.Mock()
    alsasink._device = device_mock

    alsasink.release()

    device_mock.close.assert_called_with()
    assert alsasink._device is None


def test_writedata_to_device(alsasink):
    device_mock = mock.Mock()
    alsasink._device = device_mock
    alsasink._write_data('abcd')
    device_mock.write.assert_called_once_with('abcd')


@pytest.mark.parametrize("format,expected", [
    ('little', alsaaudio.PCM_FORMAT_S16_LE),
    ("big", alsaaudio.PCM_FORMAT_S16_BE)
])
def test_sets_endian_format(alsasink, libalsa, device, format, expected):
    with mock.patch('scweb.alsa_sink.sys') as sys_mock:
        sys_mock.byteorder = format

        alsasink.acquire()

    device.setformat.assert_called_with(expected)


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

    with pytest.raises(scweb.player.PlayerError):
        alsasink.mixer_load()


def test_mixer_load_raises_if_no_mixers(alsasink, libalsa):
    libalsa.mixers.return_value = []

    with pytest.raises(scweb.player.PlayerError):
        alsasink.mixer_load()


def test_mixer_load_raises_errors(alsasink, libalsa):
    libalsa.Mixer.side_effect = alsaaudio.ALSAAudioError('error')

    with pytest.raises(scweb.player.PlayerError):
        alsasink.mixer_load()


def test_mixer_unload(alsasink, mixer):
    alsasink._mixer = mixer
    alsasink.mixer_unload()

    mixer.close.assert_called_once_with()
    alsasink._mixer = None


def test_getvolume(alsasink):
    alsasink._mixer.getvolume.return_value = [67]

    result = alsasink._getvolume()

    assert result == 67


def test_volume_set(alsasink):
    alsasink._setvolume(54)

    alsasink._mixer.setvolume.assert_called_once_with(54)


def test_getmute(alsasink):
    alsasink._mixer.getmute.return_value = [1]

    result = alsasink._getmute()

    assert result


def test_setmute(alsasink):
    alsasink._setmute(True)

    alsasink._mixer.setmute.assert_called_once_with(True)

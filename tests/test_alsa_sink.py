import unittest

from tests import mock

import alsaaudio
import spotifyconnect
import sc_console.alsa_sink

class TestAlsaSink(unittest.TestCase):

    def setUp(self):
        self.session = mock.Mock()
        self.session.player.num_listeners.return_value = 0
        spotifyconnect._session_instance = self.session
        self.alsaaudio = mock.Mock()
       
        self.sink = sc_console.alsa_sink.AlsaSink('default')

    def tearDown(self):
        spotifyconnect._session_instance = None

    def test_off_closes_audio_device(self):
        device_mock = mock.Mock()
        self.sink._device = device_mock

        self.sink.off()

        device_mock.close.assert_called_with()
        self.assertIsNone(self.sink._device)

    def test_defaults(self):
        self.assertEqual(self.sink.device_name, 'default')
        self.assertEqual(self.sink.rate, sc_console.alsa_sink.RATE)
        self.assertEqual(self.sink.channels, sc_console.alsa_sink.CHANNELS)
        self.assertEqual(self.sink.periodsize, sc_console.alsa_sink.PERIODSIZE)
        self.session.player.num_listeners.assert_called_once_with(spotifyconnect.PlayerEvent.MUSIC_DELIVERY) 
        
    def test_initialization(self):        
        self.sink = sc_console.alsa_sink.AlsaSink('other device', 100, 6, 0.43, 1348)

        self.assertEqual(self.sink.device_name, 'other device')
        self.assertEqual(self.sink.rate, 100)
        self.assertEqual(self.sink.channels, 6)
        self.assertEqual(self.sink.periodsize, 0.43)

    @mock.patch('sc_console.alsa_sink.alsa', spec=alsaaudio)
    def test_acquire_device(self, libalsa):
        device = mock.Mock()
        libalsa.PCM.return_value = device

        self.sink.acquire()

        # The ``device`` kwarg was added in pyalsaaudio 0.8
        libalsa.PCM.assert_called_with(libalsa.PCM_PLAYBACK, device='default')
        device.setrate.assert_called_with(sc_console.alsa_sink.RATE)
        device.setchannels.assert_called_with(sc_console.alsa_sink.CHANNELS)
        device.setperiodsize.assert_called_with(sc_console.alsa_sink.PERIODSIZE)

    def test_aquired_device_property_true(self):
        self.sink._device = mock.Mock()

        self.assertTrue(self.sink.acquired())

    def test_aquired_device_property_false(self):
        self.sink._device = None

        self.assertFalse(self.sink.acquired())

    @mock.patch('sc_console.alsa_sink.alsa', spec=alsaaudio)
    def test_music_delivery_creates_device_with_alsaaudio_0_7(self, libalsa):
        del libalsa.pcms  # Remove pyalsaudio 0.8 version marker
        device = mock.Mock()
        libalsa.PCM.return_value = device
        audio_format = mock.Mock()

        self.sink.acquire()

        # The ``card`` kwarg was deprecated in pyalsaaudio 0.8
        libalsa.PCM.assert_called_with(libalsa.PCM_PLAYBACK, card='default')

    @mock.patch('sc_console.alsa_sink.alsa', spec=alsaaudio)
    def test_sets_little_endian_format_if_little_endian_system(self, libalsa):
        device = mock.Mock()
        libalsa.PCM.return_value = device

        with mock.patch('sc_console.alsa_sink.sys') as sys_mock:
            sys_mock.byteorder = 'little'

            self.sink.acquire()

        device.setformat.assert_called_with(libalsa.PCM_FORMAT_S16_LE)

    @mock.patch('sc_console.alsa_sink.alsa', spec=alsaaudio)
    def test_sets_big_endian_format_if_big_endian_system(self, libalsa):
        device = mock.Mock()
        libalsa.PCM.return_value = device

        with mock.patch('sc_console.alsa_sink.sys') as sys_mock:
            sys_mock.byteorder = 'big'

            self.sink.acquire()

        device.setformat.assert_called_with(libalsa.PCM_FORMAT_S16_BE)

    def test_music_delivery_writes_frames_to_stream(self):
        self.sink._device = mock.Mock()
        self.sink.write = mock.Mock()
        audio_format = mock.Mock()
        audio_format.sample_type = spotifyconnect.SampleType.S16NativeEndian
        pending = [0]
        frames = "a" * 10000

        num_consumed_frames = self.sink._on_music_delivery(
            audio_format, 'abcd',
             mock.sentinel.num_samples, pending, mock.sentinel.session)

        self.assertEqual(num_consumed_frames, mock.sentinel.num_samples)

    @mock.patch('sc_console.alsa_sink.alsa', spec=alsaaudio)
    def test_mixer_load(self, libalsa):
        libalsa.cards.return_value = {0,'default'}
        libalsa.mixers.return_value = ['PCM']
        libalsa.Mixer.return_value = mock.sentinel.mixer

        self.sink.mixer_load()

        libalsa.mixers.assert_called_with(device='default', cardindex=-1)
        libalsa.Mixer.assert_called_with('PCM', device='default', cardindex=-1)
        self.assertEqual(self.sink._mixer, mock.sentinel.mixer)
        self.assertEqual(self.sink.volmin, 0)
        self.assertEqual(self.sink.volmax, 100)

    @mock.patch('sc_console.alsa_sink.alsa', spec=alsaaudio)
    def test_mixer_load_with_custom_mixer(self, libalsa):
        libalsa.cards.return_value = {'card0'}
        libalsa.Mixer.return_value = mock.sentinel.mixer

        self.sink.mixer_load('LineIn')

        libalsa.Mixer.assert_called_with('LineIn', device='default', cardindex=-1)
        self.assertEqual(self.sink._mixer, mock.sentinel.mixer)
        self.assertEqual(self.sink.volmin, 0)
        self.assertEqual(self.sink.volmax, 100)

    @mock.patch('sc_console.alsa_sink.alsa', spec=alsaaudio)
    def test_mixer_load_with_custom_volumes(self, libalsa):
        libalsa.cards.return_value = {0,'default'}
        libalsa.Mixer.return_value = mock.sentinel.mixer

        self.sink.mixer_load('LineIn', 20, 80)

        self.assertEqual(self.sink.volmin, 20)
        self.assertEqual(self.sink.volmax, 80)

    @mock.patch('sc_console.alsa_sink.alsa', spec=alsaaudio)
    def test_mixer_load_with_card(self, libalsa):
        self.sink.device_name = 'default:CARD=card1'
        libalsa.cards.return_value = ['card0','card1']
        libalsa.mixers.return_value = ['PCM']
        libalsa.Mixer.return_value = mock.sentinel.mixer

        self.sink.mixer_load()

        libalsa.mixers.assert_called_with(device='default', cardindex=1)
        libalsa.Mixer.assert_called_with('PCM', device='default', cardindex=1)
        self.assertEqual(self.sink._mixer, mock.sentinel.mixer)

    @mock.patch('sc_console.alsa_sink.alsa', spec=alsaaudio)
    def test_mixer_load_with_device(self, libalsa):
        self.sink.device_name = 'default:dev=surround'
        libalsa.cards.return_value = ['card0','card1']
        libalsa.mixers.return_value = ['PCM']
        libalsa.Mixer.return_value = mock.sentinel.mixer

        self.sink.mixer_load()

        libalsa.mixers.assert_called_with(device='surround', cardindex=-1)
        libalsa.Mixer.assert_called_with('PCM', device='surround', cardindex=-1)
        self.assertEqual(self.sink._mixer, mock.sentinel.mixer)

    @mock.patch('sc_console.alsa_sink.alsa', spec=alsaaudio)
    def test_mixer_load_with_device_and_card(self, libalsa):
        self.sink.device_name = 'default:CARD=card1,DEV=surround'
        libalsa.cards.return_value = ['card0','card1']
        libalsa.mixers.return_value = ['PCM']
        libalsa.Mixer.return_value = mock.sentinel.mixer

        self.sink.mixer_load()

        libalsa.mixers.assert_called_with(device='surround', cardindex=1)
        libalsa.Mixer.assert_called_with('PCM', device='surround', cardindex=1)
        self.assertEqual(self.sink._mixer, mock.sentinel.mixer)

    def test_mixer_unload(self):
        mixer = mock.Mock()
        self.sink._mixer = mixer

        self.sink.mixer_unload()

        mixer.close.assert_called_once_with()
        self.sink._mixer = None

    def test_mixer_loaded_true(self):
        self.sink._mixer = mock.Mock()

        self.assertTrue(self.sink.mixer_loaded())

    def test_aquired_device_property_false(self):
        self.sink._mixer = None

        self.assertFalse(self.sink.mixer_loaded())

    def test_playing_true(self):
        self.sink.t.isAlive = mock.Mock(return_value=True)

        self.assertTrue(self.sink.playing())

    def test_playing_true(self):
        self.sink.t.isAlive = mock.Mock(return_value=False)

        self.assertFalse(self.sink.playing())

    def test_volrange_set(self):
        self.sink.volrange_set(10,76)

        self.assertEqual(self.sink.volmin, 10)
        self.assertEqual(self.sink.volmax, 76)

    def test_volume_get_standard(self):
        mixer = mock.Mock()
        mixer.getvolume.return_value=[74]
        self.sink._mixer = mixer
        self.sink.volmax = 100
        self.sink.volmin = 0

        result = self.sink.volume_get()

        self.assertEqual(result, 74)

    def test_volume_get_with_max_value(self):
        mixer = mock.Mock()
        self.sink._mixer = mixer
        self.sink.volmax = 70
        self.sink.volmin = 0

        mixer.getvolume.return_value=[74]
        result1 = self.sink.volume_get()
        mixer.getvolume.return_value=[35]
        result2 = self.sink.volume_get()

        self.assertEqual(result1, 100)
        self.assertEqual(result2, 50)

    def test_volume_get_with_min_value(self):
        mixer = mock.Mock()
        self.sink._mixer = mixer
        self.sink.volmax = 100
        self.sink.volmin = 20

        mixer.getvolume.return_value=[10]
        result1 = self.sink.volume_get()
        mixer.getvolume.return_value=[40]
        result2 = self.sink.volume_get()

        self.assertEqual(result1, 0)
        self.assertEqual(result2, 25)

    def test_volume_get_with_min_max_value(self):
        mixer = mock.Mock()
        self.sink._mixer = mixer
        self.sink.volmax = 80
        self.sink.volmin = 20

        mixer.getvolume.return_value=[60]
        result = self.sink.volume_get()

        self.assertEqual(result, 67)

    def test_volume_set_standard(self):
        mixer = mock.Mock()
        mixer.getmute.return_value = [0]
        self.sink._mixer = mixer
        self.sink.volmax = 100
        self.sink.volmin = 0

        result = self.sink.volume_set(70)

        mixer.setvolume.assert_called_once_with(70)

    def test_volume_set_mute(self):
        mixer = mock.Mock()
        mixer.getmute.return_value = [0]
        self.sink._mixer = mixer
        self.sink.volmax = 100
        self.sink.volmin = 0

        result = self.sink.volume_set(0)

        mixer.setvolume.assert_called_once_with(0)
        mixer.setmute.assert_called_once_with(1)

    def test_volume_set_unmute(self):
        mixer = mock.Mock()
        mixer.getmute.return_value = [1]
        self.sink._mixer = mixer
        self.sink.volmax = 100
        self.sink.volmin = 0

        result = self.sink.volume_set(80)

        mixer.setvolume.assert_called_once_with(80)
        mixer.setmute.assert_called_once_with(0)

    def test_volume_set_standard_min_max(self):
        mixer = mock.Mock()
        mixer.getmute.return_value = [0]
        self.sink._mixer = mixer
        self.sink.volmax = 80
        self.sink.volmin = 20

        result = self.sink.volume_set(67)

        mixer.setvolume.assert_called_once_with(60)
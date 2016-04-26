import unittest

from tests import mock

import spotifyconnect
import sc_console.snapcast_sink


class TestSnapcastSink(unittest.TestCase):

    def setUp(self):
        self.session = mock.Mock()
        self.session.player.num_listeners.return_value = 0
        spotifyconnect._session_instance = self.session
       
        self.sink = sc_console.snapcast_sink.SnapcastSink()

    def tearDown(self):
        spotifyconnect._session_instance = None

    def test_defaults(self):
        self.assertEqual(self.sink._pipe, None)
        self.assertEqual(self.sink.namedpipe, sc_console.snapcast_sink.NAMEDPIPE)
        
    def test_initialization(self):        
        self.sink = sc_console.snapcast_sink.SnapcastSink('/false/pipe', 5000)

        self.assertEqual(self.sink.namedpipe, '/false/pipe')

    @mock.patch('sc_console.snapcast_sink.os')
    def test_off_closes_audio_device(self, mock_os):
        pipe = mock.sentinel.pipe
        self.sink._pipe = pipe
        
        self.sink.off()

        mock_os.close.assert_called_with(pipe)
        self.assertIsNone(self.sink._pipe)

    @mock.patch('sc_console.snapcast_sink.os')
    def test_acquire_device(self, mock_os):
        self.sink.namedpipe = 'named_pipe'
        mock_os.open.return_value = mock.sentinel.pipe

        self.sink.acquire()

        # The ``device`` kwarg was added in pyalsaaudio 0.8
        mock_os.open.assert_called_with('named_pipe', mock_os.O_WRONLY)
        self.assertEqual(self.sink._pipe, mock.sentinel.pipe)

    def test_aquired_device_property_true(self):
        self.sink._pipe = mock.Mock()

        self.assertTrue(self.sink.acquired())

    def test_aquired_device_property_false(self):
        self.sink._pipe = None

        self.assertFalse(self.sink.acquired())

    def test_music_delivery_writes_frames_to_stream(self):
        self.sink._pipe = mock.Mock()
        self.sink.write = mock.Mock()
        audio_format = mock.Mock()
        audio_format.sample_type = spotifyconnect.SampleType.S16NativeEndian
        pending = [0]
        frames = "a" * 10000

        num_consumed_frames = self.sink._on_music_delivery(
            audio_format, 'abcd',
             mock.sentinel.num_samples, pending, mock.sentinel.session)

        self.assertEqual(num_consumed_frames, mock.sentinel.num_samples)

    def test_playing_true(self):
        self.sink.t.isAlive = mock.Mock(return_value=True)

        self.assertTrue(self.sink.playing())

    def test_playing_true(self):
        self.sink.t.isAlive = mock.Mock(return_value=False)

        self.assertFalse(self.sink.playing())
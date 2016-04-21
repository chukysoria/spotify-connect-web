import unittest

from tests import mock

import sc_console.snapcast_sink
from sc_console.snapcast_sink import SnapcastSink


class TestSnapcastSink(unittest.TestCase):

    def test_defaults(self):

        sink = SnapcastSink()

        self.assertEqual(sink.buffer_length, sc_console.snapcast_sink.MAXPERIODS)
        self.assertEqual(sink.pipe, None)
        self.assertEqual(sink.namedpipe, sc_console.snapcast_sink.NAMEDPIPE)
        
    def test_initialization(self):
        
        sink = SnapcastSink('/false/pipe', 5000)

        self.assertEqual(sink.buffer_length, 5000)
        self.assertEqual(sink.namedpipe, '/false/pipe')
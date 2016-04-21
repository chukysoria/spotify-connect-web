import unittest

from tests import mock

import sc_console

import spotifyconnect


class test_connect_console(unittest.TestCase):
    
    def test_spotify_key_missing(self):
        
        with self.assertRaises(IOError):
            sc_console.Connect()

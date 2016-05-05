import os

import pytest

import sc_console.command


def test_createparser():
    cl = sc_console.command.CommandLineParser()
    parser = cl.createparser()
    args = parser.parse_args([])

    assert not args.debug
    key_path = os.path.join(
        os.path.dirname(
            os.path.realpath(sc_console.command.__file__)),
        'spotify_appkey.key')
    assert args.key == key_path
    assert args.username is None
    assert args.password is None
    assert args.bitrate == 160
    assert args.credentials == 'credentials.json'
    assert args.name == 'TestConnect'
    assert args.audiosink == 'alsa'
    assert args.device == 'default'
    assert args.mixer == ''
    assert args.volmin == 0
    assert args.volmax == 100


def test_createwebparser():
    cl = sc_console.command.CommandLineParser()
    parser = cl.create_web_parser()
    args = parser.parse_args([])

    assert args.cors is None


def test_createwebparser_CORS():
    cl = sc_console.command.CommandLineParser()
    parser = cl.create_web_parser()
    args = parser.parse_args(['--cors', 'http://one.direction'])

    assert args.cors == ['http://one.direction']


def test_createwebparser_raise():
    cl = sc_console.command.CommandLineParser()
    parser = cl.create_web_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['--cors', 'one.direction'])

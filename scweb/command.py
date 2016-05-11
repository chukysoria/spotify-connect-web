import argparse
import os
import re

from six.moves import range

__all__ = [
    'CommandLineParser'
]


class CommandLineParser():

    def __init__(self):
        pass

    def createparser(self, parent=None):
        if parent:
            arg_parser = argparse.ArgumentParser(
                description='Web interface for Spotify Connect',
                parents=[parent], add_help=True)
        else:
            arg_parser = argparse.ArgumentParser(
                description='Web interface for Spotify Connect', add_help=True)
        arg_parser.add_argument(
            '--debug', '-d',
            help='enable libspotify_embedded/flask debug output',
            action="store_true")
        arg_parser.add_argument(
            '--key', '-k',
            help='path to spotify_appkey.key \
            (can be obtained from \
            https://developer.spotify.com/my-account/keys )',
            default=os.path.join(
                os.path.dirname(
                    os.path.realpath(__file__)), 'spotify_appkey.key'))
        arg_parser.add_argument(
            '--username', '-u', help='your spotify username')
        arg_parser.add_argument(
            '--password', '-p', help='your spotify password')
        arg_parser.add_argument(
            '--name', '-n', help='name that shows up in the spotify client',
            default='TestConnect')
        arg_parser.add_argument(
            '--bitrate', '-b',
            help='Sets bitrate of alsa_sink stream (may not actually work)',
            choices=[90, 160, 320], type=int, default=160)
        arg_parser.add_argument(
            '--credentials', '-c',
            help='File to load and save credentials from/to',
            default='credentials.json')
        arg_parser.add_argument(
            '--audiosink', '-a',
            help='output audio to alsa device or to Snapcast',
            choices=['alsa', 'snapcast'], default='alsa')
        arg_parser.add_argument(
            '--device', '-D', help='alsa output device', default='default')
        arg_parser.add_argument('--mixer', '-m',
                                help='alsa mixer name for volume control',
                                default='')
        arg_parser.add_argument('--volmin', '-v',
                                help='minimum mixer volume (percentage)',
                                metavar='{0-99}', choices=range(0, 100),
                                type=int, default=0)
        arg_parser.add_argument('--volmax', '-V',
                                help='maximum mixer volume (percentage)',
                                metavar='{1-100}', choices=range(1, 101),
                                type=int, default=100)

        return arg_parser

    def create_web_parser(self):
        arg_parser = argparse.ArgumentParser(add_help=False)

        cors_help = (
            "enable CORS support for this host (for the web api). "
            "Must be in the format <protocol>://<hostname>:<port>. "
            "Port can be excluded if its 80 (http) or 443 (https). "
            "Can be specified multiple times"
        )

        def validate_cors_host(host):
            host_regex = re.compile(
                r'^(http|https)://[a-zA-Z0-9][a-zA-Z0-9-.]+(:[0-9]{1,5})?$')
            result = re.match(host_regex, host)
            if result is None:
                raise argparse.ArgumentTypeError(
                    '%s is not in the format <protocol>://<hostname>:<port>. \
                    Protocol must be http or https' % host)
            return host

        arg_parser.add_argument(
            '--cors', help=cors_help, action='append', type=validate_cors_host)

        return self.createparser(arg_parser)

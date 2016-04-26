#!/usr/bin/env python

import argparse
import json
import os
import signal
import sys
import uuid
from time import sleep

import player_exceptions

import spotifyconnect

import alsa_sink
import snapcast_sink

__all__=[
    'Connect'
]


class Connect:

    def _createparser(self, web_arg_parser=None):
        if web_arg_parser:
            arg_parser = argparse.ArgumentParser(
                description='Web interface for Spotify Connect',
                parents=[web_arg_parser], add_help=True)
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
                                metavar='{0-99}', choices=xrange(0, 100),
                                type=int, default=0)
        arg_parser.add_argument('--volmax', '-V',
                                help='maximum mixer volume (percentage)',
                                metavar='{1-100}', choices=xrange(1, 101),
                                type=int, default=100)

        return arg_parser

    def __init__(self, web_arg_parser=None):
        parser = self._createparser(web_arg_parser)
        args = parser.parse_args()
        self._main(args)
    
    def _main(self, args):    
        self.args = args

        self.credentials = dict({
            'device-id': str(uuid.uuid4()),
            'username': None,
            'blob': None
        })

        try:
            with open(self.args.credentials) as f:
                self.credentials.update(
                    {k: v.encode('utf-8') if isinstance(v, unicode) else v
                     for (k, v)
                     in json.loads(f.read()).iteritems()})
        except IOError:
            pass

        if self.args.username:
            self.credentials['username'] = self.args.username

        self.config = spotifyconnect.Config()
        try:
            self.config.load_application_key_file(self.args.key)
        except IOError as e:
            print("Error opening app key: {}.".format(e))
            print("If you don't have one, it can be obtained \
                   from https://developer.spotify.com/my-account/keys")
            raise e

        self.config.device_id = self.credentials['device-id']
        self.config.remote_name = self.args.name

        try:
            self.session = spotifyconnect.Session(self.config)
        except spotifyconnect.LibError as error:
            print("New spotify-connect session failed:", error.message)
            print("Exiting.")
            sys.exit(1)

        # Connection object, callbacks and events
        self.session.connection.on(
            spotifyconnect.ConnectionEvent.CONNECTION_NOTIFY_UPDATED,
            self.connection_notify)
        self.session.connection.on(
            spotifyconnect.ConnectionEvent.NEW_CREDENTIALS,
            self.connection_new_credentials)

        if self.args.debug:
            self.session.connection.on(
                spotifyconnect.DebugEvent.DEBUG_MESSAGE, self.debug_message)

        self.session.player.on(
            spotifyconnect.PlayerEvent.PLAYBACK_NOTIFY, self.playback_notify)
        self.session.player.on(
            spotifyconnect.PlayerEvent.PLAYBACK_SEEK, self.playback_seek)

        if self.args.audiosink == 'alsa':            
            self.audio_player = alsa_sink.AlsaSink(self.args.device)
        elif self.args.audiosink == 'snapcast':            
            self.audio_player = snapcast_sink.SnapcastSink()

        self.audio_player.mixer_load(self.args.mixer, volmin=self.args.volmin, volmax=self.args.volmax)
        self.session.player.on(
            spotifyconnect.PlayerEvent.PLAYBACK_VOLUME, self.volume_set)

        mixer_volume = self.audio_player.volume_get()
        self.session.player.volume = mixer_volume

        if self.args.bitrate == 90:
            bitrate = spotifyconnect.Bitrate.BITRATE_90k
        elif self.args.bitrate == 160:
            bitrate = spotifyconnect.Bitrate.BITRATE_160k
        elif self.args.bitrate == 320:
            bitrate = spotifyconnect.Bitrate.BITRATE_320k
        self.session.player.set_bitrate(bitrate)

        self.print_zeroconf_vars(self.session.get_zeroconf_vars())

        if self.credentials['username'] and self.args.password:
            self.session.connection.login(
                self.credentials['username'], password=self.args.password)
        elif self.credentials['username'] and self.credentials['blob']:
            self.session.connection.login(
                self.credentials['username'], blob=self.credentials['blob'])

        self.playback_session = PlaybackSession()

        self.event_loop = spotifyconnect.EventLoop(self.session)
        self.event_loop.start()

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    # Connection callbacks
    def connection_notify(self, notify, session):
        print(notify._name)

    def connection_new_credentials(self, blob, session):
        print(blob)
        self.credentials['blob'] = blob

        zeroconf = session.get_zeroconf_vars()
        self.credentials['username'] = zeroconf.active_user

        with open(self.args.credentials, 'w') as f:
            f.write(json.dumps(self.credentials))

    # Debug callbacks
    def debug_message(self, msg, session):
        print(msg)

    # Playback callbacks
    def playback_notify(self, notify, session):

        # TODO: Check that device is active
        if notify == spotifyconnect.PlaybackNotify.Play:
            print("kSpPlaybackNotifyPlay")
            if self.playback_session.active:
                if not self.audio_player.acquired():
                    try:
                        self.audio_player.acquire()
                        print("DeviceAcquired")
                        self.audio_player.play()
                    except player_exceptions.PlayerError as error:
                        print(error)
                        session.player.pause()
                else:
                    self.audio_player.play()

        elif notify == spotifyconnect.PlaybackNotify.Pause:
            print("kSpPlaybackNotifyPause")
            if self.audio_player.playing():
                self.audio_player.pause()
                self.audio_player.release()
                print("DeviceReleased")

        elif notify == spotifyconnect.PlaybackNotify.TrackChanged:
            print("kSpPlaybackNotifyTrackChanged")
        elif notify == spotifyconnect.PlaybackNotify.Next:
            print("kSpPlaybackNotifyNext")
        elif notify == spotifyconnect.PlaybackNotify.Prev:
            print("kSpPlaybackNotifyPrev")
        elif notify == spotifyconnect.PlaybackNotify.ShuffleEnabled:
            print("kSpPlaybackNotifyShuffleEnabled")
        elif notify == spotifyconnect.PlaybackNotify.ShuffleDisabled:
            print("kSpPlaybackNotifyShuffleDisabled")
        elif notify == spotifyconnect.PlaybackNotify.RepeatEnabled:
            print("kSpPlaybackNotifyRepeatEnabled")
        elif notify == spotifyconnect.PlaybackNotify.RepeatDisabled:
            print("kSpPlaybackNotifyRepeatDisabled")
        elif notify == spotifyconnect.PlaybackNotify.BecameActive:
            print("kSpPlaybackNotifyBecameActive")
            self.playback_session.activate()
        elif notify == spotifyconnect.PlaybackNotify.BecameInactive:
            print("kSpPlaybackNotifyBecameInactive")
            self.playback_session.deactivate()
            if self.audio_player.acquired():
                self.audio_player.pause()
                self.audio_player.release()
                print("DeviceReleased")
        elif notify == spotifyconnect.PlaybackNotify.PlayTokenLost:
            print("kSpPlaybackNotifyPlayTokenLost")
        elif notify == spotifyconnect.PlaybackNotify.AudioFlush:
            print("kSpPlaybackEventAudioFlush")
            if self.audio_player.acquired():
                self.audio_player.buffer_flush()
        else:
            print("UNKNOWN PlaybackNotify {}".format(notify))

    def volume_set(self, volume, session):
        print("volume: {}".format(volume))
        self.audio_player.volume_set(volume)

    def playback_seek(self, millis, session):
        print("playback_seek: {}".format(millis))

    def signal_handler(self, signal, frame):
        self.event_loop.stop()
        self.session.connection.logout()
        self.session.free_session()
        sys.exit(0)

    def print_zeroconf_vars(self, zeroconf_vars):
        print("public key: {}".format(zeroconf_vars.public_key))
        print("device id: {}".format(zeroconf_vars.device_id))
        print("remote name: {}".format(zeroconf_vars.remote_name))
        print("account req: {}".format(zeroconf_vars.account_req))
        print("device type: {}".format(zeroconf_vars.device_type))


class PlaybackSession:

    def __init__(self):
        self._active = False

    @property
    def active(self):
        return self._active

    def activate(self):
        self._active = True

    def deactivate(self):
        self._active = False


# First run the command
# avahi-publish-service TestConnect _spotify-connect._tcp 4000
# VERSION=1.0 CPath=/login/_zeroconf
#
# Only run if script is run directly and not by an import
if __name__ == "__main__":
    connect = Connect()
    zeroconfserver = spotifyconnect.AvahiZeroConfServer(4000)
    zeroconfserver.run()

    while True:
        sleep(5)

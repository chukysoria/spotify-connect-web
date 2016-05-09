from __future__ import unicode_literals

import json
import os
import signal
import sys
import uuid

import six

import spotifyconnect

from sc_console.alsa_sink import AlsaSink
from sc_console.player import PlayerError
from sc_console.snapcast_sink import SnapcastSink

__all__ = [
    'Connect'
]


class Connect:

    def __init__(
            self,
            key=None,
            username=None,
            password=None,
            name='TestConnect',
            bitrate=160,
            credentials='credentials.json',
            audiosink='alsa',
            device='default',
            mixer=None,
            volmin=0,
            volmax=100,
            debug=False):

        if key is None:
            key = os.path.join(os.path.dirname(
                os.path.realpath(__file__)), 'spotify_appkey.key')

        self._credentials = dict({
            'device-id': str(uuid.uuid4()),
            'username': None,
            'blob': None
        })

        self.credential_file = credentials
        try:
            with open(self.credential_file) as f:
                self._credentials.update(
                    {k: v.encode('utf-8') if isinstance(v, str) else v
                     for (k, v)
                     in six.iteritems(json.loads(f.read()))})
        except IOError:
            pass

        if username:
            self._credentials['username'] = username

        self.config = spotifyconnect.Config()
        try:
            self.config.load_application_key_file(key)
        except IOError as e:
            print("Error opening app key: {}.".format(e))
            print("If you don't have one, it can be obtained \
                   from https://developer.spotify.com/my-account/keys")
            raise e

        self.config.device_id = self._credentials['device-id']
        self.config.remote_name = name

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

        if debug:
            self.session.connection.on(
                spotifyconnect.DebugEvent.DEBUG_MESSAGE, self.debug_message)

        self.session.player.on(
            spotifyconnect.PlayerEvent.PLAYBACK_NOTIFY, self.playback_notify)
        self.session.player.on(
            spotifyconnect.PlayerEvent.PLAYBACK_SEEK, self.playback_seek)

        if audiosink == 'alsa':
            self.audio_player = AlsaSink(device)
        elif audiosink == 'snapcast':
            self.audio_player = SnapcastSink()

        self.audio_player.mixer_load(mixer, volmin=volmin, volmax=volmax)
        self.session.player.on(
            spotifyconnect.PlayerEvent.PLAYBACK_VOLUME, self.volume_set)

        mixer_volume = self.audio_player.volume_get()
        self.session.player.volume = mixer_volume

        if bitrate == 90:
            sp_bitrate = spotifyconnect.Bitrate.BITRATE_90k
        elif bitrate == 160:
            sp_bitrate = spotifyconnect.Bitrate.BITRATE_160k
        elif bitrate == 320:
            sp_bitrate = spotifyconnect.Bitrate.BITRATE_320k
        self.session.player.set_bitrate(sp_bitrate)

        self.print_zeroconf_vars(self.session.get_zeroconf_vars())

        if self._credentials['username'] and password:
            try:
                self.session.connection.login(
                    self._credentials['username'],
                    password=password)
            except spotifyconnect.LibError as e:
                print('Error when login with password: {}'.format(e.message))
        elif self._credentials['username'] and self._credentials['blob']:
            try:
                self.session.connection.login(
                    self._credentials['username'],
                    blob=self._credentials['blob'])
            except spotifyconnect.LibError as e:
                print('Error when login with blob: {}'.format(e.message))

        self.playback_session = PlaybackSession()

        self.event_loop = spotifyconnect.EventLoop(self.session)
        self.event_loop.start()

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    _credentials = None
    credential_file = None
    audio_player = None
    session = None
    config = None

    # Connection callbacks
    def connection_notify(self, notify, session):
        print(notify._name)

    def connection_new_credentials(self, blob, session):
        print(blob)
        self._credentials['blob'] = blob

        zeroconf = session.get_zeroconf_vars()
        self._credentials['username'] = zeroconf.active_user

        with open(self.credential_file, 'w') as f:
            f.write(json.dumps(self._credentials))

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
                    except PlayerError as error:
                        print(error)
                        session.player.pause()
                else:
                    self.audio_player.play()

        elif notify == spotifyconnect.PlaybackNotify.Pause:
            print("kSpPlaybackNotifyPause")
            if self.audio_player.acquired():
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

    def signal_handler(self, signal, frame):  # pragma: no cover
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

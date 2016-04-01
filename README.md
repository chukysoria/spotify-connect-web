# Spotify Connect Web

This is based on the implementation of Fornoth from https://github.com/Fornoth/spotify-connect-web modified so it uses the [pyspotify-connect](https://github.com/chukysoria/pyspotify-connect) wrapper.

## Installation
Copy `libspotify_embedded_shared.so` to `\usr\lib`.
Run `pip install -r requirements.txt`.

### Pyalsaaudio
Can either be installed via `pip` (requires the ALSA headers (`libasound2-dev` package on Debian/Ubuntu)) or the `python-alsaaudio` package on Debian/Ubuntu.

## Usage
Tested against the rocki `libspotify_embedded_shared.so`
```
usage: main.py [-h] [--debug] [--key KEY] [--username USERNAME]
               [--password PASSWORD] [--name NAME] [--bitrate {90,160,320}]
               [--credentials CREDENTIALS] [--device DEVICE] [--mixer MIXER]
               [--volmin {0-99}] [--volmax {1-100}]

Web interface for Spotify Connect

optional arguments:
  -h, --help            show this help message and exit
  --debug, -d           enable libspotify_embedded/flask debug output
  --key KEY, -k KEY     path to spotify_appkey.key
  --username USERNAME, -u USERNAME
                        your spotify username
  --password PASSWORD, -p PASSWORD
                        your spotify password
  --name NAME, -n NAME  name that shows up in the spotify client
  --bitrate {90,160,320}, -b {90,160,320}
                        Sets bitrate of alsa_sink stream (may not actually
                        work)
  --credentials CREDENTIALS, -c CREDENTIALS
                        File to load and save credentials from/to
  --device DEVICE, -D DEVICE
                        alsa output device
  --mixer MIXER, -m MIXER
                        alsa mixer name for volume control
  --volmin {0-99}, -v {0-99}
                        minimum mixer volume (percentage)
  --volmax {1-100}, -V {1-100}
                        maximum mixer volume (percentage)

```

The program requires a spotify premium account, and the `spotify_appkey.key` (the binary version) file needs to be obtained from https://developer.spotify.com/my-account/keys , and needs to placed in the python scripts directory, or have the path specified with the `-k` parameter.

###Device parameter

The alsa output device name should be as returned by the `pyalsaaudio` command `pcms`. In order to check the possible valid options please execute:

    import alsaaudio
    alsaaudio.pcms()


### Launching
- Running with debug output `python main.py -d`
- Can also be run without the web server (Requires username and password to be passed in as parameters or enable zeroconf)  `python connect_console.py`

### Headers
Generated with `cpp spotify.h > spotify.processed.h && sed -i 's/__extension__//g' spotify.processed.h`
`spotify.h` was taken from from https://github.com/plietar/spotify-connect

## Web server
Server runs on port `4000`

### Logging in
There's a login button on the webpage to enter a username and password, or zeroconf (avahi) login can be used after executing the command `avahi-publish-service TestConnect _spotify-connect._tcp 4000 VERSION=1.0 CPath=/login/_zeroconf` (`avahi-publish-service` is in the `avahi-utils` package).

If you want to execute the above command as a service do the following:

	cp ./daemons/avahi_service/spotifyconnect.service to /etc/avahi/services/spotifyconnect.service

It will start to be working as soon the file is copied, there's no need to restart.

After logging in successfully, a blob is sent by Spotify and saved to disk (to `credentials.json` by default), and is use to login automatically on next startup.

### Daemons
If you want to always run on startup follow this steps (for Raspeberry 1 with armel on chroot):
	
	cp ./daemons/chroot_sysvinit/spotify-connect /etc/init.d/spotify-connect
	chmod +x /etc/init.d/spotify-connect
	update-rc.d spotify-connect defaults	


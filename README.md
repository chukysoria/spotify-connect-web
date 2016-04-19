# Spotify Connect Web

This is based on the implementation of Fornoth from https://github.com/Fornoth/spotify-connect-web modified so it uses the [pyspotify-connect](https://github.com/chukysoria/pyspotify-connect) wrapper.

## Installation

Follow this instructions for Debian:
	
	sudo apt-get update
	sudo apt-get install git build-essential  
	sudo apt-get install libasound2-dev python-dev python-gevent
	git checkout https://github.com/chukysoria/spotify-connect-web.git
	cd spotify-connect-web

For armv6-armel systems:
	
	wget https://github.com/sashahilton00/spotify-connect-resources/raw/master/libs/armel/armv6/release-esdk-1.18.0-v1.18.0-g121b4b2b/libspotify_embedded_shared.so

For armv7-armhf systems (Raspeberry Pi 2):

	wget https://github.com/sashahilton00/spotify-connect-resources/raw/master/libs/armhf/armv7/release-esdk-1.20.0-v1.20.0-g594175d4/libspotify_embedded_shared.so

Finally:
	
	sudo mv libspotify_embedded_shared.so /usr/lib
	pip install -r requirements.txt
	
## Usage
```
usage: main.py [-h] [--cors CORS] [--debug] [--key KEY] [--username USERNAME]
               [--password PASSWORD] [--name NAME] [--bitrate {90,160,320}]
               [--credentials CREDENTIALS] [--audiosink {alsa,snapcast}]
               [--device DEVICE] [--mixer MIXER] [--volmin {0-99}]
               [--volmax {1-100}]


Web interface for Spotify Connect

optional arguments:
  -h, --help            show this help message and exit
  --cors CORS           enable CORS support for this host (for the web api).
                        Must be in the format <protocol>://<hostname>:<port>.
                        Port can be excluded if its 80 (http) or 443 (https).
                        Can be specified multiple times  
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
  --audiosink {alsa,snapcast}, -a {alsa,snapcast}
                        output audio to alsa device or to Snapcast
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

The alsa output device name should be as returned by the `pyalsaaudio` command `pcms`. In order to check the possible valid options please execute on a Python console:

    import alsaaudio
    alsaaudio.pcms()


### Launching
- Running with debug output `python main.py -d`
- Can also be run without the web server (Requires username and password to be passed in as parameters or enable avahi-zeroconf)  `python connect_console.py`

### Headers
Generated with `cpp spotify.h > spotify.processed.h && sed -i 's/__extension__//g' spotify.processed.h`
`spotify.h` was taken from from https://github.com/plietar/spotify-connect

## Web server
Server runs on port `4000`

### Logging in
There's a login button on the webpage to enter a username and password, or zeroconf (avahi) login can be used after executing the command `avahi-publish-service TestConnect _spotify-connect._tcp 4000 VERSION=1.0 CPath=/login/_zeroconf` (`avahi-publish-service` is in the `avahi-utils` package).

If you want to execute the above command as a service do the following:

	cp ./daemons/avahi_service/spotifyconnect.service /etc/avahi/services/spotifyconnect.service

It will start to be working as soon the file is copied, there's no need to restart.

After logging in successfully, a blob is sent by Spotify and saved to disk (to `credentials.json` by default), and is use to login automatically on next startup.

### Daemons
If you want to always run on startup follow this steps (for Raspeberry 1 with armel on chroot):
	
	sudo cp ./daemons/chroot_sysvinit/spotify-connect /etc/init.d/spotify-connect
	sudo chmod +x /etc/init.d/spotify-connect
	sudo update-rc.d spotify-connect defaults	


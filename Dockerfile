FROM chukysoria/rpi-python-testing:armv7-py27
MAINTAINER Carlos Sánchez

RUN [ "cross-build-start" ]

ADD https://github.com/sashahilton00/spotify-connect-resources/raw/master/libs/armhf/armv7/release-esdk-1.20.0-v1.20.0-g594175d4/libspotify_embedded_shared.so /usr/lib/
COPY . /usr/src/app
WORKDIR /usr/src/app
RUN  python setup.py install                                            && \
     rm -rf /tmp/* /var/tmp/*

RUN [ "cross-build-end" ]

WORKDIR /usr/data

CMD [ "-b320", "-nSpotifyConnectWeb"] 
ENTRYPOINT [ "spotifyconnect-web", "-k/usr/data/spotify_appkey.key" ]

EXPOSE 4000
VOLUME /usr/data

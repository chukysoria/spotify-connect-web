FROM chukysoria/rpi-python-testing:armv7
MAINTAINER Carlos Sánchez

WORKDIR /usr/src/app

ADD https://github.com/sashahilton00/spotify-connect-resources/raw/master/libs/armhf/armv7/release-esdk-1.20.0-v1.20.0-g594175d4/libspotify_embedded_shared.so /usr/lib/
COPY requirements.txt /usr/src/app/
RUN pip install coveralls tox && pip install -r requirements.txt

ENTRYPOINT ["/bin/bash"]

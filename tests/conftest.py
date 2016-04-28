import pytest
import spotifyconnect
from tests import mock
import sc_console
import os
import alsaaudio

@pytest.fixture()
def sp_session():
    session = mock.Mock()
    session.player.num_listeners.return_value = 0
    spotifyconnect._session_instance = session

    return session

@pytest.yield_fixture
def snapcast_os():
    patcher = mock.patch.object(sc_console.snapcast_sink, 'os')
    yield patcher.start()
    patcher.stop()


@pytest.fixture
def snapsink(sp_session):
    sink = sc_console.snapcast_sink.SnapcastSink()

    return sink

@pytest.fixture
def mixer():
    mixer = mock.Mock(spec=alsaaudio.Mixer)
    mixer.getmute.return_value = [0]

    return mixer    

@pytest.fixture
def device():
    device = mock.Mock(spec=alsaaudio.PCM)

    return device

@pytest.yield_fixture()
def libalsa():
    patcher = mock.patch.object(sc_console.alsa_sink, 'alsa')    
    yield patcher.start()
    patcher.stop()

@pytest.fixture
def alsasink(sp_session, libalsa, device, mixer):
    libalsa.cards.return_value = ['card0','card1']
    libalsa.PCM.return_value = device
    libalsa.mixers.return_value = ['PCM']
    libalsa.Mixer.return_value = mixer
    libalsa.PCM_FORMAT_S16_LE = alsaaudio.PCM_FORMAT_S16_LE
    libalsa.PCM_FORMAT_S16_BE = alsaaudio.PCM_FORMAT_S16_BE
    sink = sc_console.alsa_sink.AlsaSink()
    sink.mixer_load()

    return sink    
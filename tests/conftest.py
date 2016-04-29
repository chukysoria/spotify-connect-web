import pytest
import spotifyconnect
from tests import mock
import sc_console
import os
import alsaaudio

@pytest.fixture()
def sp_session():
    session = mock.Mock(spec=spotifyconnect.Session)
    session.player.num_listeners.return_value = 0
    spotifyconnect._session_instance = session

    return session

@pytest.fixture
def sp_config():
    config = mock.Mock(spec=spotifyconnect.Config)
    return config

@pytest.fixture
def connect(request, libspotify, sp_session, sp_config, alsasink_module, mock_alsasink, sp_eventloop, openfile, snapcast_module, snapsink):
    libspotify.Config.return_value = sp_config
    libspotify.Session.return_value = sp_session
    libspotify.EventLoop.return_value = sp_eventloop
    alsasink_module.AlsaSink.return_value = mock_alsasink
    snapcast_module.SnapcastSink.return_value = snapsink
    file_data = '{}'
    try:
        file_data = getattr(request.function.credentials_file, "args")[0]
    except AttributeError:
        pass
    finally:
        openfile.side_effect = mock.mock_open(read_data=file_data)

    try:
        args = getattr(request.function.commandline, "args")[0]
    except AttributeError:
        args = []
    finally:        
        parser = sc_console.connect._createparser()
        args = parser.parse_args(args)
        connect = sc_console.Connect(parsedargs=args)      

    return connect

@pytest.yield_fixture
def openfile():
    patcher = mock.patch.object(sc_console.connect, 'open')
    yield patcher.start()
    patcher.stop()
        
@pytest.yield_fixture
def libspotify():
    patcher = mock.patch.object(sc_console.connect, 'spotifyconnect')
    yield patcher.start()
    patcher.stop()

@pytest.fixture
def sp_zeroconf():
    zc = spotifyconnect.Zeroconf(mock.Mock())
    zc.public_key = 'pulic key'
    zc.device_id = 'device id'
    zc.active_user = 'active user'
    zc.remote_name = 'remote name'
    zc.account_req = 'premium'
    zc.device_type = 'device type'
    zc.library_version = 'library version'
    
    return zc

@pytest.yield_fixture
def alsasink_module():
    patcher = mock.patch.object(sc_console.connect, 'alsa_sink')
    yield patcher.start()
    patcher.stop()

@pytest.yield_fixture
def snapcast_module():
    patcher = mock.patch.object(sc_console.connect, 'snapcast_sink')
    yield patcher.start()
    patcher.stop()

@pytest.fixture
def sp_eventloop():
    event_loop = mock.Mock(spec = spotifyconnect.EventLoop)

    return event_loop

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
    mixer.getvolume.return_value = [38]

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
def mock_alsasink(sp_session, libalsa, device, mixer):
    sink = mock.Mock(spec=sc_console.alsa_sink.AlsaSink())
    
    return sink    

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
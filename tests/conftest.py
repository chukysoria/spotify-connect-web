import alsaaudio

import pytest

import spotifyconnect

import sc_console

from tests import mock


@pytest.fixture()
def sp_session(sp_zeroconf):
    session = mock.Mock(spec=spotifyconnect.Session)
    session.player.num_listeners.return_value = 0
    session.get_zeroconf_vars.return_value = sp_zeroconf
    spotifyconnect._session_instance = session

    return session


@pytest.fixture
def sp_config():
    config = mock.Mock(spec=spotifyconnect.Config)
    config.brand_name = "Brand Name"
    config.model_name = "Model Name"
    return config


@pytest.fixture
def connect(
        request,
        libspotify,
        sp_session,
        sp_config,
        alsasink_class,
        mock_alsasink,
        sp_eventloop,
        openfile,
        snaspcast_class,
        snapsink):
    libspotify.Config.return_value = sp_config
    libspotify.Session.return_value = sp_session
    libspotify.EventLoop.return_value = sp_eventloop
    libspotify.PlaybackNotify = spotifyconnect.PlaybackNotify
    alsasink_class.return_value = mock_alsasink
    snaspcast_class.return_value = snapsink
    file_data = '{}'
    try:
        file_data = getattr(request.function.credentials_file, "args")[0]
    except AttributeError:
        pass
    finally:
        openfile.side_effect = mock.mock_open(read_data=file_data)

    try:
        cmd_args = getattr(request.function.commandline, "args")[0]
    except AttributeError:
        cmd_args = []
    finally:
        parser = sc_console.CommandLineParser().createparser()
        kwargs = vars(parser.parse_args(cmd_args))
        with mock.patch('sc_console.connect.open', openfile, create=True):
            connect = sc_console.Connect(**kwargs)

    return connect


@pytest.fixture
def openfile():
    m = mock.mock_open()
    return m


@pytest.yield_fixture
def libspotify():
    patcher = mock.patch.object(sc_console.connect, 'spotifyconnect')
    yield patcher.start()
    patcher.stop()


@pytest.fixture
def sp_zeroconf():
    zc = mock.Mock(spec=spotifyconnect.Zeroconf)
    zc.public_key = 'public key'
    zc.device_id = 'device id'
    zc.active_user = 'active user'
    zc.remote_name = 'remote name'
    zc.account_req = 'premium'
    zc.device_type = 'device type'
    zc.library_version = 'library version'

    return zc


@pytest.yield_fixture
def alsasink_class():
    patcher = mock.patch.object(sc_console.connect, 'AlsaSink')
    yield patcher.start()
    patcher.stop()


@pytest.yield_fixture
def snaspcast_class():
    patcher = mock.patch.object(sc_console.connect, 'SnapcastSink')
    yield patcher.start()
    patcher.stop()


@pytest.fixture
def sp_eventloop():
    event_loop = mock.Mock(spec=spotifyconnect.EventLoop)

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
    libalsa.cards.return_value = ['card0', 'card1']
    libalsa.PCM.return_value = device
    libalsa.mixers.return_value = ['PCM']
    libalsa.Mixer.return_value = mixer
    libalsa.PCM_FORMAT_S16_LE = alsaaudio.PCM_FORMAT_S16_LE
    libalsa.PCM_FORMAT_S16_BE = alsaaudio.PCM_FORMAT_S16_BE
    libalsa.ALSAAudioError = alsaaudio.ALSAAudioError
    sink = sc_console.alsa_sink.AlsaSink()
    sink.mixer_load()

    return sink


@pytest.fixture
def player(sp_session):
    player = sc_console.player.Player(buffer_length=50)
    player.release = mock.Mock()
    player._getvolume = mock.Mock()
    player._getvolume.return_value = 38
    player._setvolume = mock.Mock()
    player._getmute = mock.Mock()
    player._getmute.return_value = False
    player._setmute = mock.Mock()

    return player


@pytest.fixture
def mock_connect(sp_session, sp_config):
    mock_connect = mock.Mock(spec=sc_console.connect)
    mock_connect.session = sp_session
    mock_connect.config = sp_config
    return mock_connect


@pytest.fixture
def webapp(mock_connect):
    flask_app = sc_console.app.app
    flask_app.config['CONNECT_APP'] = mock_connect
    client = flask_app.test_client()

    return client

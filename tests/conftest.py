import pytest
import spotifyconnect
from tests import mock
import sc_console
import os

@pytest.fixture
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
    
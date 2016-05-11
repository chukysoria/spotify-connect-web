from __future__ import unicode_literals

import json

import pytest

import spotifyconnect

import scweb.app


def test_playblack_play(webapp, sp_player):
    rv = webapp.get('/api/playback/play')

    assert rv.status_code == 204
    sp_player.play.assert_called_once_with()


def test_playblack_pause(webapp, sp_player):
    rv = webapp.get('/api/playback/pause')

    assert rv.status_code == 204
    sp_player.pause.assert_called_once_with()


def test_playblack_prev(webapp, sp_player):
    rv = webapp.get('/api/playback/prev')

    assert rv.status_code == 204
    sp_player.skip_to_prev.assert_called_once_with()


def test_playblack_next(webapp, sp_player):
    rv = webapp.get('/api/playback/next')

    assert rv.status_code == 204
    sp_player.skip_to_next.assert_called_once_with()


def test_playblack_shuffle(webapp, sp_player):
    rv = webapp.get('/api/playback/shuffle')

    assert rv.status_code == 204
    sp_player.enable_shuffle.assert_called_once_with()


def test_playblack_repeat(webapp, sp_player):
    rv = webapp.get('/api/playback/repeat')

    assert rv.status_code == 204
    sp_player.enable_repeat.assert_called_once_with()


def test_playback_volume(webapp):
    data = webapp.get('/api/playback/volume').data.decode()
    result = json.loads(data)

    assert result['volume'] == 38


def test_playback_volume_post(webapp, sp_player):
    rv = webapp.post('/api/playback/volume', data=dict(
        value='48'))

    assert rv.status_code == 204
    assert sp_player.volume == 48


def test_playback_volume_post_raise_error(webapp):
    rv = webapp.post('/api/playback/volume')
    result = json.loads(rv.data.decode())

    assert rv.status_code == 400
    assert result['error'] == 'value must be set'

'''
def test_metadata(webapp, sp_player):
    data = webapp.get('/api/info/metadata').data.decode()
    result = json.loads(data)

    assert result['playlist_name'] == 'playlist_name'
    assert result['playlist_uri'] == 'playlist_uri'
    assert result['track_name'] == 'track_name'
    assert result['track_uri'] == 'track_uri'
    assert result['artist_name'] == 'artist_name'
    assert result['artist_uri'] == 'artist_uri'
    assert result['album_name'] == 'album_name'
    assert result['album_uri'] == 'album_uri'
    assert result['cover_uri'] == 'cover_uri'
    assert result['volume'] == 38
    assert result['cover_url_small'] == '/url/to/image'
'''


def test_status(webapp):
    data = webapp.get('/api/info/status').data.decode()
    result = json.loads(data)

    assert result['active']
    assert result['playing']
    assert result['shuffle']
    assert result['repeat']
    assert result['logged_in']


def test_display_name(webapp):
    data = webapp.get('/api/info/display_name').data.decode()
    result = json.loads(data)

    assert result['remoteName'] == 'remote name'


def test_display_name_post(webapp, sp_session):
    rv = webapp.post('/api/info/display_name', data=dict(
        displayName='new name'))

    assert rv.status_code == 204
    sp_session.set_remote_name.assert_called_with('new name')


def test_display_name_post_raise_error(webapp):
    rv = webapp.post('/api/info/display_name')
    result = json.loads(rv.data.decode())

    assert rv.status_code == 400
    assert result['error'] == 'displayName must be set'


def test_login_logout(webapp, sp_session):
    rv = webapp.get('/login/logout')

    sp_session.connection.logout.assert_called_once_with()
    assert rv.headers['Location'] == 'http://localhost/'
    assert rv.status_code == 302


def test_login_password(webapp, sp_session):
    rv = webapp.post('/login/password', data=dict(
        userName='foo',
        password='bar'))

    sp_session.connection.login.asssert_called_once_with('foo', 'bar')
    assert rv.headers['Location'] == 'http://localhost/'
    assert rv.status_code == 302


def test_login_password_errors(webapp, sp_session):
    rv = webapp.post('/login/password', data=dict(
        userName='foo'))
    rv2 = webapp.post('/login/password', data=dict(
        password='foo'))

    sp_session.connection.login.asssert_not_called()
    assert rv.headers['Location'] == 'http://localhost/'
    assert rv.status_code == 302
    assert rv2.headers['Location'] == 'http://localhost/'
    assert rv2.status_code == 302


@pytest.mark.parametrize('invalid, state, finished, success', [
    (False, 1, False, False),
    (False, 0, True, True),
    (True, 0, True, False)
])
def test_check_login(webapp, sp_session, invalid, state, finished, success):
    sp_session.connection.connection_state = state
    if invalid:
        scweb.app.error_notification(
            spotifyconnect.ErrorType.LoginBadCredentials,
            sp_session)

    data = webapp.get('/login/check_login').data.decode()
    result = json.loads(data)

    assert result['finished'] == finished
    assert result['success'] == success


def test_login_zeroconf_empty_get(webapp):
    data = webapp.get('/login/_zeroconf').data.decode()
    result = json.loads(data)

    assert result['status'] == 301
    assert result['spotifyError'] == 0
    assert result['statusString'] == 'ERROR-MISSING-ACTION'


def test_login_zeroconf_wrong_action(webapp):
    data = webapp.get('/login/_zeroconf?action=foo').data.decode()
    result = json.loads(data)

    assert result['status'] == 301
    assert result['spotifyError'] == 0
    assert result['statusString'] == 'ERROR-INVALID-ACTION'


def test_login_zeroconf_get_info(webapp):
    data = webapp.get('/login/_zeroconf?action=getInfo').data.decode()
    result = json.loads(data)

    assert result['status'] == 101
    assert result['spotifyError'] == 0
    assert result['activeUser'] == 'active user'
    assert result['brandDisplayName'] == 'Brand Name'
    assert result['accountReq'] == 'premium'
    assert result['deviceID'] == 'device id'
    assert result['publicKey'] == 'public key'
    assert result['version'] == '2.0.1'
    assert result['deviceType'] == 'device type'
    assert result['modelDisplayName'] == 'Model Name'
    assert result['statusString'] == 'ERROR-OK'
    assert result['remoteName'] == 'remote name'


def test_login_zeroconf_post_user(webapp, mock_connect):
    data = webapp.post('/login/_zeroconf?action=addUser', data=dict(
        userName='foo',
        blob='longstring',
        clientKey='longkey')).data.decode()
    result = json.loads(data)

    assert result['status'] == 101
    assert result['spotifyError'] == 0
    assert result['statusString'] == 'ERROR-OK'
    mock_connect.session.connection.login.assert_called_once_with(
        'foo', zeroconf=('longstring', 'longkey'))

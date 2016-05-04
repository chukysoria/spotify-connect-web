from __future__ import unicode_literals

import json


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


def test_login_zeroconf_get_info(webapp, mock_connect):
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

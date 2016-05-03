import os
from time import sleep

from flask import (Flask, flash, jsonify, redirect,
                   render_template, request, url_for)
from flask_bootstrap import Bootstrap

import spotifyconnect

app = Flask('SpotifyConnectWeb')
Bootstrap(app)

# Serve bootstrap files locally instead of from a CDN
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
app.secret_key = os.urandom(24)


def get_connect_app():
    return app.config['CONNECT_APP']

# Error notification
# Used by the error callback to determine login status
invalid_login = False


def error_notification(error_type, session):
    global invalid_login
    if error_type == spotifyconnect.ErrorType.LoginBadCredentials:
        invalid_login = True

# #Routes

# Home page


@app.route('/')
def index():
    return render_template('index.html')

# #API routes

# Playback routes


@app.route('/api/playback/play')
def playback_play():
    get_connect_app().session.player.play()
    return '', 204


@app.route('/api/playback/pause')
def playback_pause():
    get_connect_app().session.player.pause()
    return '', 204


@app.route('/api/playback/prev')
def playback_prev():
    get_connect_app().session.player.skip_to_prev()
    return '', 204


@app.route('/api/playback/next')
def playback_next():
    get_connect_app().session.player.skip_to_next()
    return '', 204


@app.route('/api/playback/shuffle')
def playback_shuffle():
    get_connect_app().session.player.enable_shuffle()
    return '', 204


@app.route('/api/playback/repeat')
def playback_repeat():
    get_connect_app().session.player.enable_repeat()
    return '', 204


@app.route('/api/playback/volume', methods=['GET'])
def playback_volume_get():
    return jsonify({
        'volume': get_connect_app().session.player.volume
    })


@app.route('/api/playback/volume',
           methods=['POST'], endpoint='playback_volume-post')
def playback_volume_set():
    volume = request.form.get('value')
    if volume is None:
        return jsonify({
            'error': 'value must be set'
        }), 400
    get_connect_app().session.player.volume = int(volume)
    return '', 204

# Info routes


@app.route('/api/info/metadata')
def info_metadata():
    try:
        track = get_connect_app().session.player.current_track
        res = track.__dict__
        res['_sp_metadata'] = ''
        res['volume'] = get_connect_app().session.player.volume
        res['cover_url_small'] = track.get_image_url(
            spotifyconnect.ImageSize.Normal)
        return jsonify(res)
    except spotifyconnect.Error:
        res = dict()
        res['track_name'] = 'Not playing'
        res['album_name'] = ''
        res['artist_name'] = ''
    finally:
        return jsonify(res)


@app.route('/api/info/status')
def info_status():
    return jsonify({
        'active': bool(get_connect_app().session.player.active_device),
        'playing': bool(get_connect_app().session.player.playing),
        'shuffle': bool(get_connect_app().session.player.shuffled),
        'repeat': bool(get_connect_app().session.player.repeated),
        'logged_in': not bool(
            get_connect_app().session.connection.connection_state)
    })


@app.route('/api/info/display_name', methods=['GET'])
def info_display_name_get():
    return jsonify({
        'remoteName': get_zeroconf_vars()['remote_name']
    })


@app.route('/api/info/display_name',
           methods=['POST'], endpoint='display_name-post')
def info_display_name_set():
    display_name = str(request.form.get('displayName'))
    if not display_name:
        return jsonify({
            'error': 'displayName must be set'
        }), 400
    get_connect_app().session.set_remote_name(display_name)
    return '', 204

# Login routes


@app.route('/login/logout')
def login_logout():
    get_connect_app().session.connection.logout()
    return redirect(url_for('index'))


@app.route('/login/password', methods=['POST'])
def login_password():
    global invalid_login
    invalid_login = False
    username = str(request.form.get('username'))
    password = str(request.form.get('password'))

    if not username or not password:
        flash('Username or password not specified', 'danger')
    else:
        flash('Waiting for spotify', 'info')
        get_connect_app().session.connection.login(username, password=password)
        sleep

    return redirect(url_for('index'))


@app.route('/login/check_login')
def check_login():
    res = {
        'finished': False,
        'success': False
    }

    if invalid_login:
        res['finished'] = True
    elif bool(get_connect_app().session.connection.connection_state):
        res['finished'] = True
        res['success'] = True

    return jsonify(res)


@app.route('/login/_zeroconf', methods=['GET', 'POST'])
def login_zeroconf():
    action = request.args.get('action') or request.form.get('action')
    if not action:
        return jsonify({
            'status': 301,
            'spotifyError': 0,
            'statusString': 'ERROR-MISSING-ACTION'})
    if action == 'getInfo' and request.method == 'GET':
        return get_info()
    elif action == 'addUser' and request.method == 'POST':
        return add_user()
    else:
        return jsonify({
            'status': 301,
            'spotifyError': 0,
            'statusString': 'ERROR-INVALID-ACTION'})


def get_info():
    zeroconf_vars = get_connect_app().session.get_zeroconf_vars()

    return jsonify({
        'status': 101,
        'spotifyError': 0,
        'activeUser': zeroconf_vars.active_user,
        'brandDisplayName': get_connect_app().config.brand_name,
        'accountReq': zeroconf_vars.account_req,
        'deviceID': zeroconf_vars.device_id,
        'publicKey': zeroconf_vars.public_key,
        'version': '2.0.1',
        'deviceType': zeroconf_vars.device_type,
        'modelDisplayName': get_connect_app().config.model_name,
        # Status codes are ERROR-OK (not actually an error),
        # ERROR-MISSING-ACTION, ERROR-INVALID-ACTION, ERROR-SPOTIFY-ERROR,
        # ERROR-INVALID-ARGUMENTS, ERROR-UNKNOWN, and ERROR_LOG_FILE
        'statusString': 'ERROR-OK',
        'remoteName': zeroconf_vars.remote_name,
    })


def add_user():
    args = request.form
    # TODO: Add parameter verification
    username = str(args.get('userName'))
    blob = str(args.get('blob'))
    clientKey = str(args.get('clientKey'))

    get_connect_app().session.connection.login(
        username, zeroconf=(blob, clientKey))

    return jsonify({
        'status': 101,
        'spotifyError': 0,
        'statusString': 'ERROR-OK'
    })

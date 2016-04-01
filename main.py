#!/usr/bin/env python

# First run the command avahi-publish-service TestConnect _spotify-connect._tcp 4000 VERSION=1.0 CPath=/login/_zeroconf
# TODO: Add error checking
import os
import argparse
import re

from flask import Flask, request, abort, jsonify, render_template, redirect, flash, url_for

from connect_console import Connect
from flask_bootstrap import Bootstrap
from flask.ext.cors import CORS
from gevent.wsgi import WSGIServer
import spotifyconnect

web_arg_parser = argparse.ArgumentParser(add_help=False)

#Not a tuple, evaluates the same as "" + ""
cors_help = (
    "enable CORS support for this host (for the web api). "
    "Must be in the format <protocol>://<hostname>:<port>. "
    "Port can be excluded if its 80 (http) or 443 (https). "
    "Can be specified multiple times"
)

def validate_cors_host(host):
    host_regex = re.compile(r'^(http|https)://[a-zA-Z0-9][a-zA-Z0-9-.]+(:[0-9]{1,5})?$')
    result = re.match(host_regex, host)
    if result is None:
         raise argparse.ArgumentTypeError('%s is not in the format <protocol>://<hostname>:<port>. Protocol must be http or https' % host)
    return host

web_arg_parser.add_argument('--cors', help=cors_help, action='append', type=validate_cors_host)
args = web_arg_parser.parse_known_args()[0]

app = Flask(__name__)
Bootstrap(app)
#Add CORS headers to API requests for specified hosts
CORS(app, resources={r"/api/*": {"origins": args.cors}})

# Serve bootstrap files locally instead of from a CDN
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
app.secret_key = os.urandom(24)

# Used by the error callback to determine login status
invalid_login = False

connect_app = Connect(web_arg_parser)

def error_notification(error_type, session):
    global invalid_login
    if error_type == spotifyconnect.ErrorType.LoginBadCredentials:
        invalid_login = True

connect_app.session.connection.on(spotifyconnect.ConnectionEvent.ERROR_NOTIFICATION, error_notification)

if os.environ.get('DEBUG') or connect_app.args.debug:
    app.debug = True

# #Routes

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# #API routes

# Playback routes
@app.route('/api/playback/play')
def playback_play():
    connect_app.session.player.play()
    return '', 204

@app.route('/api/playback/pause')
def playback_pause():
    connect_app.session.player.pause()
    return '', 204

@app.route('/api/playback/prev')
def playback_prev():
    connect_app.session.player.skip_to_prev()
    return '', 204

@app.route('/api/playback/next')
def playback_next():
    connect_app.session.player.skip_to_next()
    return '', 204

@app.route('/api/playback/shuffle')
def playback_shuffle():
    connect_app.session.player.enable_shuffle()
    return '', 204

@app.route('/api/playback/repeat')
def playback_repeat():
    connect_app.session.player.enable_repeat()
    return '', 204

@app.route('/api/playback/volume', methods=['GET'])
def playback_volume():
    return jsonify({
        'volume': connect_app.session.player.volume
    })

@app.route('/api/playback/volume', methods=['POST'], endpoint='playback_volume-post')
def playback_volume():
    volume = request.form.get('value')
    if volume is None:
        return jsonify({
            'error': 'value must be set'
        }), 400
    connect_app.session.player.volume = int(volume)
    return '', 204

# Info routes
@app.route('/api/info/metadata')
def info_metadata():
    track = connect_app.session.player.current_track
    res = track.__dict__
    res['volume'] = connect_app.session.player.volume
    res['cover_url_small'] = track.get_image_url(spotifyconnect.ImageSize.Normal)
    return jsonify(res)

@app.route('/api/info/status')
def info_status():
    return jsonify({
        'active': bool(connect_app.session.player.active_device),
        'playing': bool(connect_app.session.player.playing),
        'shuffle': bool(connect_app.session.player.shuffled),
        'repeat': bool(connect_app.session.player.repeated),
        'logged_in': bool(connect_app.session.connection.connection_state)
    })

@app.route('/api/info/display_name', methods=['GET'])
def info_display_name():
    return jsonify({
        'remoteName': get_zeroconf_vars()['remote_name']
    })

@app.route('/api/info/display_name', methods=['POST'], endpoint='display_name-post')
def info_display_name():
    display_name = str(request.form.get('displayName'))
    if not display_name:
        return jsonify({
            'error': 'displayName must be set'
        }), 400
    connect_app.session.set_remote_name(display_name)
    return '', 204

# Login routes
@app.route('/login/logout')
def login_logout():
    connec_app.session.connection.logout()
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
        connect_app.session.connection.login(username, password=password)
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
    elif bool(connect_app.session.connection.connection_state):
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
    zeroconf_vars = connect_app.session.get_zeroconf_vars()

    return jsonify({
        'status': 101,
        'spotifyError': 0,
        'activeUser': zeroconf_vars.active_user,
        'brandDisplayName': connect_app.config.brand_name,
        'accountReq': zeroconf_vars.account_req,
        'deviceID': zeroconf_vars.device_id,
        'publicKey': zeroconf_vars.public_key,
        'version': '2.0.1',
        'deviceType': zeroconf_vars.device_type,
        'modelDisplayName': connect_app.config.model_name,
        # Status codes are ERROR-OK (not actually an error), ERROR-MISSING-ACTION, ERROR-INVALID-ACTION, ERROR-SPOTIFY-ERROR, ERROR-INVALID-ARGUMENTS, ERROR-UNKNOWN, and ERROR_LOG_FILE
        'statusString': 'ERROR-OK',
        'remoteName': zeroconf_vars.remote_name,
    })

def add_user():
    args = request.form
    # TODO: Add parameter verification
    username = str(args.get('userName'))
    blob = str(args.get('blob'))
    clientKey = str(args.get('clientKey'))

    connect_app.session.connection.login(username, zeroconf=(blob, clientKey))

    return jsonify({
        'status': 101,
        'spotifyError': 0,
        'statusString': 'ERROR-OK'
        })



# Only run if script is run directly and not by an import
if __name__ == "__main__":
# Can be run on any port as long as it matches the one used in avahi-publish-service
    http_server = WSGIServer(('', 4000), app)
    http_server.serve_forever()

# TODO: Add signal catcher
connect_app.session.free_session()

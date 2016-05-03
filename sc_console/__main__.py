#!/usr/bin/env python
import os
import sys
from time import sleep

from flask_cors import CORS

import spotifyconnect

import sc_console
import sc_console.app


def main():

    command_line = sc_console.CommandLineParser()
    parser = command_line.createparser()
    parsedargs = vars(parser.parse_args())
    sc_console.Connect(**parsedargs)
    zeroconfserver = spotifyconnect.AvahiZeroConfServer(4000)
    zeroconfserver.run()
    while True:
        sleep(5)

def main_web():
    parser_classs = sc_console.CommandLineParser()
    parser = parser_classs.create_web_parser()
    args = parser.parse_args()

    connect_app = sc_console.Connect(key=args.key,
                                     username=args.username,
                                     password=args.password,
                                     name=args.name,
                                     bitrate=args.bitrate,
                                     credentials=args.credentials,
                                     audiosink=args.audiosink,
                                     device=args.device,
                                     mixer=args.mixer,
                                     volmin=args.volmin,
                                     volmax=args.volmax,
                                     debug=args.debug)

    flask_app = sc_console.app.app
    # Add CORS headers to API requests for specified hosts
    CORS(flask_app, resources={r"/api/*": {"origins": args.cors}})

    if os.environ.get('DEBUG') or args.debug:
        flask_app.debug = True

    flask_app.config['CONNECT_APP'] = connect_app

    connect_app.session.connection.on(
        spotifyconnect.ConnectionEvent.ERROR_NOTIFICATION,
        sc_console.app.error_notification)
    # Can be run on any port as long as it matches the one used in
    # avahi-publish-service
    flask_app.run('0.0.0.0', port=4000, use_reloader=False, debug=True)

    # TODO: Add signal catcher
    connect_app.session.free_session()

# First run the command
# avahi-publish-service TestConnect _spotify-connect._tcp 4000
# VERSION=1.0 CPath=/login/_zeroconf
#
# Only run if script is run directly and not by an import
if __name__ == "__main__":
    sys.exit(main_web())

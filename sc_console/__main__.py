#!/usr/bin/env python
import sys
from time import sleep

import spotifyconnect

import sc_console


def main():

    command_line = sc_console.CommandLineParser()
    parser = command_line.createparser()
    parsedargs = vars(parser.parse_args())
    sc_console.Connect(**parsedargs)
    zeroconfserver = spotifyconnect.AvahiZeroConfServer(4000)
    zeroconfserver.run()
    while True:
        sleep(5)

# First run the command
# avahi-publish-service TestConnect _spotify-connect._tcp 4000
# VERSION=1.0 CPath=/login/_zeroconf
#
# Only run if script is run directly and not by an import
if __name__ == "__main__":
    sys.exit(main())

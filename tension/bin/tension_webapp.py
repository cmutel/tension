#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tension webapp.

Usage:
  tension_webapp [--port=<port>] [--localhost]
  tension_webapp -h | --help
  tension_webapp --version

Options:
  --localhost   Only allow connections from this computer.
  -h --help     Show this screen.
  --version     Show version.

"""
from docopt import docopt
from tension.webapp import tension_app


def main():
    args = docopt(__doc__, version="Tension webapp 1.0")
    port = int(args.get("--port", False) or 5000)
    host = "localhost" if args.get("--localhost", False) else "0.0.0.0"

    print("tension webapp started on {}:{}".format(host, port))

    tension_app.run(host=host, port=port, debug=True)


if __name__ == "__main__":
    main()

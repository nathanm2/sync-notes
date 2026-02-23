#!/usr/bin/env python3

#
# A script that works on one or more local git repositories.  If the
# repository is "dirty", it will create a commit and then push this
# commit to a remote repository.
#
# I wanted a convenient script to backup notes stored in git repositories.
#

import configparser
import argparse
import os
import sys
import logging

logger = logging.getLogger(__name__)

class Error(Exception):
    pass

def parse_args():
    prog = os.path.basename(sys.argv[0])
    xdg_config = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    default_config = os.path.join(xdg_config, prog.removesuffix(".py"), "config.ini")

    parser = argparse.ArgumentParser(prog=prog,
        description="Automatically commit and push one or more git repositories.")

    parser.add_argument("-v", "--verbose", help="Increase logging verbosity.")
    parser.add_argument("-c", "--config", default=default_config, metavar="<config>",
                        help=f"Config file [default: {default_config}]")

    args = parser.parse_args()
    logging.basicConfig(format='%(levelname)s: %(message)s')

    if not os.path.exists(args.config):
        raise Error(f"no config: {args.config}")

    return args

def main():
    try:
        args = parse_args()
        ini_parser = configparser.ConfigParser()
        ini_parser.read(args.config)
    except Error as e:
        logger.error(str(e))

if __name__ == "__main__":
    main()

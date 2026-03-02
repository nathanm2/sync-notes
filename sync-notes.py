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
import subprocess
import logging
from datetime import datetime


class Error(Exception):
    pass

RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
RESET = '\033[0m'


class ProgLog:
    def __init__(self, level=logging.INFO, journald_prefix=False):
        self.level = level

        if journald_prefix:
            self.error_prefix = "<3>"
            self.warning_prefix = "<4>"
            self.info_prefix = "<6>"
            self.debug_prefix = "<7>"
        else:
            self.info_prefix = ""

            if sys.stderr.isatty():
                self.error_prefix = f"{RED}error:{RESET} "
                self.warning_prefix = f"{YELLOW}warning:{RESET} "
                self.debug_prefix = f"{GREEN}debug:{RESET} "
            else:
                self.error_prefix = "error: "
                self.warning_prefix = "warning: "
                self.debug_prefix = "debug: "

    def error(self, msg):
        if self.level <= logging.ERROR:
            print(f"{self.error_prefix}{msg}", file=sys.stderr)

    def warning(self, msg):
        if self.level <= logging.WARNING:
            print(f"{self.warning_prefix}{msg}", file=sys.stderr)

    def info(self, msg):
        if self.level <= logging.INFO:
            print(f"{self.info_prefix}{msg}", file=sys.stdout)

    def debug(self, msg):
        if self.level <= logging.DEBUG:
            print(f"{self.debug_prefix}{msg}", file=sys.stderr)


logger = ProgLog()

def parse_args():
    prog = os.path.basename(sys.argv[0])
    xdg_config = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    default_config = os.path.join(xdg_config, prog.removesuffix(".py"), "config.ini")

    # Setup argument parser.
    parser = argparse.ArgumentParser(prog=prog,
        description="Automatically commit and push one or more git repositories.")

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Display debug information.")
    parser.add_argument("-j", "--journal", action="store_true",
                        help="Prefix logs with journald log level (<PRIORITY>).")
    parser.add_argument("-c", "--config", default=default_config, metavar="<config>",
                        help=f"Config file [default: {default_config}]")

    # Parse arguments.
    args = parser.parse_args()

    # Re-configure the logger:
    level = logging.DEBUG if args.verbose else logging.INFO

    global logger
    logger = ProgLog(level = level, journald_prefix = args.journal)

    # Check that the config file exists.
    if not os.path.exists(args.config):
        raise Error(f"no config: {args.config}")

    return args

def parse_config(config):
    try:
        ini_parser = configparser.ConfigParser()
        ini_parser.read(config)
        return ini_parser
    except (configparser.Error, OSError) as e:
        raise Error(str(e)) from e

def run_cmd(cmd, check=False):
    """Run a command and (possibly) log its output."""

    logger.debug(" ".join(cmd))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.stdout:
        logger.debug(result.stdout.rstrip())

    if check and result.returncode != 0:
        msg = f"command failed: {' '.join(cmd)}, rc={result.returncode}"
        if logger.level > logging.DEBUG and result.stdout:
            msg += f"\n{result.stdout.rstrip()}"
        raise Error(msg)

    return result

def run_git(repo_path, *args):
    """Run a git command in 'repo_path' and raise Error if it fails."""
    cmd = ["git", "-C", repo_path, *args]
    return run_cmd(cmd, check=True)

def sync_repo(repo_name, repo_meta, commit_msg):
    logger.info(f"syncing: {repo_name}")

    repo_path = repo_meta.get("path")
    if not repo_path:
        raise Error(f"{repo_name} is missing 'path'")
    repo_path = os.path.expanduser(os.path.expandvars(repo_path))

    remote_name = repo_meta.get("remote", "origin")
    remote_branch = repo_meta.get("remote_branch", "main")

    result = run_git(repo_path, "status", "--porcelain")
    is_dirty = bool(result.stdout.strip())

    if is_dirty:
        run_git(repo_path, "add", ".")
        run_git(repo_path, "commit", "-m", commit_msg)
        run_git(repo_path, "pull", "--rebase", remote_name, remote_branch)
        run_git(repo_path, "push", remote_name, f"HEAD:{remote_branch}")
    else:
        run_git(repo_path, "pull", "--rebase", remote_name, remote_branch)

def main():
    try:
        args = parse_args()
        config = parse_config(args.config)
        commit_msg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        had_errors = 0
        for repo_name in config.sections():
            try:
                sync_repo(repo_name, dict(config.items(repo_name)), commit_msg)
            except Error as e:
                logger.error(str(e))
                had_errors = 1
    except Error as e:
        logger.error(str(e))
        had_errors = 1

    return had_errors

if __name__ == "__main__":
    sys.exit(main())

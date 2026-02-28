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

logger = logging.getLogger("sync-notes")

# Syslog/journald priority (severity) for each logging level
_JOURNAL_PRIORITY = {
    logging.DEBUG: 7,
    logging.INFO: 6,
    logging.WARNING: 4,
    logging.ERROR: 3,
    logging.CRITICAL: 2,
}


class JournalFormatter(logging.Formatter):
    """Format log records with a journald log level prefix <PRIORITY>."""

    def format(self, record):
        priority = _JOURNAL_PRIORITY.get(record.levelno, 6)
        msg = super().format(record)
        return f"<{priority}>{msg}"


class Error(Exception):
    pass

def parse_args():
    prog = os.path.basename(sys.argv[0])
    xdg_config = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    default_config = os.path.join(xdg_config, prog.removesuffix(".py"), "config.ini")

    # Setup argument parser.
    parser = argparse.ArgumentParser(prog=prog,
        description="Automatically commit and push one or more git repositories.")

    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Increase log verbosity.")
    parser.add_argument("-j", "--journal", action="store_true",
                        help="Prefix logs with journald log level (<PRIORITY>).")
    parser.add_argument("-c", "--config", default=default_config, metavar="<config>",
                        help=f"Config file [default: {default_config}]")

    # Parse arguments.
    args = parser.parse_args()

    # Setup logging.
    logging.basicConfig(stream=sys.stderr)

    if args.verbose == 1:
        logging.root.setLevel(logging.INFO)
    elif args.verbose > 1:
        logging.root.setLevel(logging.DEBUG)
    else:
        logging.root.setLevel(logging.WARNING)

    if args.journal:
        for h in logging.root.handlers:
            h.setFormatter(JournalFormatter('%(message)s'))

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

def run_cmd(cmd):
    """Run a command and (possibly) log its output."""
    log = logger.isEnabledFor(logging.DEBUG)

    if log:
        logger.debug(" ".join(cmd))

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    if log and result.stdout:
        for line in result.stdout.rstrip().splitlines():
            logger.debug(line)

    return result

def run_git(repo_path, *args):
    """Run a git command in 'repo_path' and raise Error if it fails."""
    cmd = ["git", "-C", repo_path, *args]
    result = run_cmd(cmd)
    if result.returncode != 0:
        msg = f"{' '.join(cmd)} failed with exit code {result.returncode}"
        if result.stdout and not logger.isEnabledFor(logging.DEBUG):
            msg += f"\n{result.stdout.rstrip()}"
        raise Error(msg)
    return result

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


def log_error(msg):
    for line in msg.splitlines():
        logger.error(line)

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
                log_error(str(e))
                had_errors = 1
    except Error as e:
        log_error(str(e))
        had_errors = 1

    return had_errors

if __name__ == "__main__":
    sys.exit(main())

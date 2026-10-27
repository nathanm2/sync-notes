# sync-notes

A simple Python script to synchronize text notes stored in Git repositories.

## Prerequisites

- Python 3
- Git

## Setup

The script uses an INI file at `${XDG_CONFIG_HOME}/sync-notes/config.ini` to determine
which Git repositories to sync. If `XDG_CONFIG_HOME` is not set, it defaults to
`~/.config/sync-notes/config.ini`.

Each Git repository has its own section. The section name can be anything you'd
like. Each section supports the following properties:

| Property | Required | Description | Default |
| --- | --- | --- | --- |
| `path` | Yes | Path to the local Git repository. | — |
| `remote` | No | Name of the Git remote. | `origin` |
| `remote_branch` | No | Name of the remote branch. | `main` |

### Example configuration

```ini
[notes]
path = ~/notes
remote = origin
remote_branch = main
```

## Scheduled sync

See the [systemd setup guide](systemd/README.md) to run sync-notes automatically
with a service and timer.

# systemd service and timer

Runs `sync-notes.py` once per day (06:00) as a **user** service.

## Install (user service)

1. Edit `sync-notes.service` and set `ExecStart=` to the full path of your Python 3 and `sync-notes.py` (e.g. `/usr/bin/python3 /home/nathanm/src/sync-notes/sync-notes.py`).

2. Copy units to your user systemd directory:
   ```bash
   mkdir -p ~/.config/systemd/user
   cp systemd/sync-notes.service systemd/sync-notes.timer ~/.config/systemd/user/
   ```

3. Enable and start the timer (not the service):
   ```bash
   systemctl --user daemon-reload
   systemctl --user enable --now sync-notes.timer
   ```

4. Check status:
   ```bash
   systemctl --user list-timers
   systemctl --user status sync-notes.timer
   ```

## Optional: run as system service

To install for all users, copy the units to `/etc/systemd/system/`, edit paths and `User=`, then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sync-notes.timer
```

## Schedule

Default: every day at 06:00. Change `OnCalendar=` in `sync-notes.timer` (e.g. `*-*-* 02:30:00` for 02:30). See `man systemd.time`.

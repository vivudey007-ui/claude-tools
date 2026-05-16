---
name: clapwake
description: >
  Manage the clap-wake system — double clap to wake Claude. Use when Vivaan
  asks to start, stop, check status, or troubleshoot the clap listener.
  Trigger: "clap wake", "start clap", "stop listener", "clap status".
audience: creators
category: tool
---

# Clap Wake — Double Clap to Wake Claude

## What It Does
Double clap within 0.8s → macOS notification + Terminal opens with Claude briefing.

## File Locations
| File | Path |
|---|---|
| Listener | `~/.claude/tools/clap_listener.py` |
| Start script | `~/.claude/tools/start_clapwake.sh` |
| LaunchAgent plist | `~/Library/LaunchAgents/com.vivaan.clapwake.plist` |
| Log | `~/.claude/tools/clapwake.log` |
| Error log | `~/.claude/tools/clapwake.error.log` |

## Config (inside clap_listener.py)
| Setting | Default | Meaning |
|---|---|---|
| `CLAP_THRESHOLD` | `0.3` | Volume level to count as clap (0.0–1.0) |
| `DOUBLE_CLAP_WINDOW` | `0.8s` | Max gap between 2 claps |
| `MIN_GAP` | `0.15s` | Min gap (prevents double-count) |
| `COOLDOWN` | `5.0s` | Ignore window after trigger |

## Commands

### Start listener
```bash
bash ~/.claude/tools/start_clapwake.sh
```

### Stop listener
```bash
pkill -f clap_listener.py
```

### Check if running
```bash
pgrep -f clap_listener.py && echo "RUNNING" || echo "STOPPED"
```

### View live log
```bash
tail -f ~/.claude/tools/clapwake.log
```

### Enable auto-start on login
```bash
launchctl load ~/Library/LaunchAgents/com.vivaan.clapwake.plist
```

### Disable auto-start
```bash
launchctl unload ~/Library/LaunchAgents/com.vivaan.clapwake.plist
```

## Troubleshoot

**Mic permission denied:**
System Settings → Privacy & Security → Microphone → enable Terminal

**Claps not detected:**
Lower `CLAP_THRESHOLD` to `0.2` in `clap_listener.py`

**Too many false triggers:**
Raise `CLAP_THRESHOLD` to `0.4` or lower `DOUBLE_CLAP_WINDOW` to `0.6`

**Module not found (sounddevice/numpy):**
```bash
pip3 install sounddevice numpy
```

# Claude Tools — Vivaan's Automation Stack

Tools built for Vivaan's Claude Code setup. Each tool extends Claude with hardware triggers and intelligent briefings.

## Tools

### Clap Wake (`clap_listener.py`)
Double clap within 0.8s → macOS notification + Claude briefing launches in Terminal.

**Setup:**
```bash
pip3 install sounddevice numpy
bash start_clapwake.sh
```

**Auto-start on login:**
```bash
cp launchagents/com.vivaan.clapwake.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.vivaan.clapwake.plist
```

**Config (edit in clap_listener.py):**
- `CLAP_THRESHOLD` — sensitivity (0.3 default, lower = more sensitive)
- `DOUBLE_CLAP_WINDOW` — max gap between claps (0.8s default)
- `COOLDOWN` — ignore window after trigger (5s default)

---

### Daily Briefing (`briefing.py`)
Time-aware Claude briefing: Morning kickoff / Midday accountability / Evening wrap.
Tracks BMW goal (₹50L by March 9, 2027). Auto-called by clap_listener.

**Run manually:**
```bash
python3 briefing.py
```

---

## Claude Code Skills

Skills live in `~/.claude/skills/`. See the DEY Marketing repo for all skill files.

| Persona | Trigger | Role |
|---|---|---|
| Arya / ARIA | `Arya,` or `ARIA,` | Premium web designer |
| Rohan | `Rohan,` | Meta ads strategist |
| Clap Wake | `clap wake` | Manage clap listener |

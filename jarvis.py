#!/usr/bin/env python3
"""
JARVIS — Vivaan's voice computer agent
Usage:
  python3 jarvis.py --single   → listen for ONE command then exit
  python3 jarvis.py --always   → stay active until "stop"

Triggered by clap_listener:
  3 claps → --single
  4 claps → --always
"""

import speech_recognition as sr
import subprocess
import sys
import time
import threading
import json
import os
import glob
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, date

# ─── Config ───────────────────────────────────────────────────

CLAUDE_BIN    = "/Users/vivaandey/.local/bin/claude"
SKILLS_DIR    = "/Users/vivaandey/.claude/skills"
VOICE         = "Daniel"
SPEECH_RATE   = 190
BMW_TARGET    = 5000000
BMW_DEADLINE  = date(2027, 3, 9)

WAKE_WORDS  = ["jarvis", "hey jarvis", "yo jarvis", "okay jarvis", "ok jarvis"]
STOP_WORDS  = ["stop", "jarvis stop", "hey jarvis stop", "shut up", "quiet", "enough"]
NEWS_FEED   = "https://feeds.bbci.co.uk/news/rss.xml"

MODE = "single"
for arg in sys.argv[1:]:
    if "--always" in arg:
        MODE = "always"
    elif "--single" in arg:
        MODE = "single"

# ─── Global state ─────────────────────────────────────────────

_speaking_proc  = None
_speaking_lock  = threading.Lock()
_running        = True   # set False to exit always-on loop


# ─── Utilities ────────────────────────────────────────────────

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def play_sound(name):
    subprocess.Popen(["afplay", f"/System/Library/Sounds/{name}.aiff"])


def stop_speaking():
    global _speaking_proc
    with _speaking_lock:
        if _speaking_proc and _speaking_proc.poll() is None:
            _speaking_proc.terminate()
            _speaking_proc = None
            log("Speech interrupted.")


def speak(text):
    global _speaking_proc
    clean = (text
        .replace("**", "").replace("*", "")
        .replace("`", "").replace("#", "")
        .replace('"', "'").replace("—", ",")
        .replace("₹", "rupees ").replace("\n", ". "))
    with _speaking_lock:
        proc = subprocess.Popen(["say", "-v", VOICE, "-r", str(SPEECH_RATE), clean])
        _speaking_proc = proc
    proc.wait()


def notify(msg):
    subprocess.Popen([
        "osascript", "-e",
        f'display notification "{msg}" with title "JARVIS"'
    ])


# ─── Skills Loader ────────────────────────────────────────────

def load_skills_summary() -> str:
    """Read all skill files and return a compact summary for the prompt."""
    lines = []
    for path in sorted(glob.glob(f"{SKILLS_DIR}/*.md")):
        try:
            with open(path) as f:
                content = f.read()
            # Extract name and description from frontmatter
            name, desc = "", ""
            for line in content.splitlines():
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip()
                elif line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip()
                if name and desc:
                    break
            if name:
                lines.append(f"- {name}: {desc[:120]}")
        except Exception:
            pass
    return "\n".join(lines) if lines else "No skills loaded."


# ─── News Fetcher ─────────────────────────────────────────────

def fetch_news(max_items=6) -> str:
    """Fetch BBC top headlines via RSS. Returns formatted string."""
    try:
        req = urllib.request.Request(NEWS_FEED, headers={"User-Agent": "JARVIS/1.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            tree = ET.parse(resp)
        root = tree.getroot()
        items = root.findall(".//item")[:max_items]
        headlines = []
        for item in items:
            title = item.findtext("title", "").strip()
            desc  = item.findtext("description", "").strip()
            if title:
                headlines.append(f"{title}. {desc[:80]}" if desc else title)
        return "\n".join(headlines) if headlines else ""
    except Exception as e:
        log(f"News fetch failed: {e}")
        return ""


# ─── Context Builder ──────────────────────────────────────────

def build_context() -> str:
    days_left     = (BMW_DEADLINE - date.today()).days
    daily_target  = BMW_TARGET / max(days_left, 1)
    hour          = datetime.now().hour
    tod           = "morning" if hour < 12 else ("afternoon" if hour < 18 else "evening")

    log_path = f"/Users/vivaandey/.claude/daily-log/{date.today().isoformat()}.md"
    try:
        with open(log_path) as f:
            today_log = f.read()[:500]
    except FileNotFoundError:
        today_log = "No log yet."

    skills = load_skills_summary()

    return f"""You are JARVIS — Vivaan's personal AI voice agent. British, precise, confident. Tony Stark's JARVIS.

IDENTITY RULES:
- Call him "sir" or "Vivaan" — never casual slang
- Answer directly in spoken English — no markdown, no bullets, no asterisks
- Never redirect — YOU handle it. Never say "you should open X yourself"
- 2-4 sentences for answers unless detail is clearly needed
- Be decisive. Pick the best tool, don't list options.

VIVAAN'S CONTEXT:
- Date: {date.today().strftime('%B %d, %Y')}, {tod}
- BMW Goal: rupees 50 lakhs by March 9, 2027 — {days_left} days left, rupees {daily_target:,.0f}/day needed
- Business: DEY Marketing — ad agency + web dev. Clients pay rupees 15K-35K/month
- Agents: Arya (web designer), Rohan (Meta ads strategist)

TODAY'S LOG:
{today_log}

VIVAAN'S APP TOOLKIT (installed and used regularly):
- Code/Dev: VS Code, Terminal, Claude Code (claude CLI)
- Design: Figma, Canva
- Browser: Google Chrome, Safari
- Productivity: Notion, Notes, Calendar, Reminders
- Communication: WhatsApp, Slack, Gmail (via Chrome)
- Media: Spotify, YouTube (via Chrome), QuickTime Player
- Video editing: iMovie, CapCut (if installed)
- Meetings: Zoom, FaceTime, Google Meet (via Chrome)
- Finance: Numbers, Excel (if installed)
- Social/Ads: Meta Ads Manager (via Chrome → facebook.com/adsmanager)
- Files: Finder, Downloads, Desktop
- Other: Preview (images/PDFs), TextEdit, Activity Monitor

SMART APP SELECTION GUIDE (use this intelligence):
- Writing code / building websites → VS Code + Terminal + Claude Code
- Designing visuals / logo / UI → Figma or Canva
- Running Meta ads / Facebook ads → Chrome → facebook.com/adsmanager
- Client proposal / document → Notion or Notes
- Video call / meeting → Zoom or Google Meet
- Music / focus → Spotify
- Quick note → Notes app
- Spreadsheet / numbers → Numbers
- Edit image → Preview or Figma
- Edit video → iMovie or CapCut
- Checking emails → Chrome → gmail.com
- Managing calendar / schedule → Calendar app
- Checking files → Finder
- Marketing task needing Claude → VS Code + Claude Code terminal

AVAILABLE SKILLS:
{skills}
"""


# ─── Action Executor ──────────────────────────────────────────

def execute_action(action: dict) -> str:
    t = action.get("type", "answer")
    p = action.get("payload", "")

    try:
        if t == "open_app":
            subprocess.Popen(["open", "-a", p])
            return f"Opening {p}."

        elif t == "open_url":
            subprocess.Popen(["open", p])
            return f"Opening that now."

        elif t == "web_search":
            query = str(p).replace(" ", "+")
            subprocess.Popen(["open", f"https://www.google.com/search?q={query}"])
            return f"Searching Google for {p}."

        elif t == "youtube_search":
            query = str(p).replace(" ", "+")
            subprocess.Popen(["open", f"https://www.youtube.com/results?search_query={query}"])
            return f"Pulling up {p} on YouTube."

        elif t == "open_folder":
            subprocess.Popen(["open", os.path.expanduser(str(p))])
            return f"Opening {p}."

        elif t == "open_file":
            subprocess.Popen(["open", os.path.expanduser(str(p))])
            return f"Opening that file."

        elif t == "volume_set":
            subprocess.run(["osascript", "-e", f"set volume output volume {int(p)}"])
            return f"Volume set to {p} percent."

        elif t == "volume_up":
            subprocess.run(["osascript", "-e",
                "set volume output volume (output volume of (get volume settings) + 10)"])
            return "Volume up."

        elif t == "volume_down":
            subprocess.run(["osascript", "-e",
                "set volume output volume (output volume of (get volume settings) - 10)"])
            return "Volume down."

        elif t == "mute":
            subprocess.run(["osascript", "-e", "set volume with output muted"])
            return "Muted."

        elif t == "screenshot":
            path = f"/Users/vivaandey/Desktop/screenshot_{datetime.now().strftime('%H%M%S')}.png"
            subprocess.run(["screencapture", "-x", path])
            subprocess.Popen(["open", path])
            return "Screenshot saved to Desktop."

        elif t == "lock":
            subprocess.run(["pmset", "displaysleepnow"])
            return "Locking screen."

        elif t == "terminal_command":
            cmd = str(p)
            blocked = ["rm -rf", "sudo rm", "mkfs", "dd if="]
            if any(b in cmd for b in blocked):
                return "That command is too destructive, sir. I won't run it."
            safe_cmd = cmd.replace('"', '\\"')
            apple_script = f'''
            tell application "Terminal"
                activate
                do script "{safe_cmd}"
            end tell
            '''
            subprocess.Popen(["osascript", "-e", apple_script])
            return f"Running in Terminal."

        elif t == "execute_task":
            # Open VS Code + Claude Code + type the task
            task = str(p)
            threading.Thread(target=_launch_task_in_claude, args=(task,), daemon=True).start()
            return f"On it, sir. Opening VS Code and Claude now."

        elif t == "news":
            # Fetch live headlines and send to Claude to narrate
            headlines = fetch_news()
            if not headlines:
                return str(p)  # fall back to Claude's own answer
            return _narrate_news(headlines)

        elif t == "sequence":
            # Chain multiple actions: payload = list of action dicts
            steps = p if isinstance(p, list) else []
            confirm = action.get("confirm", "Done, sir.")
            for step in steps:
                try:
                    delay = step.pop("delay", 0)
                    if delay:
                        time.sleep(delay)
                    execute_action(step)
                except Exception as se:
                    log(f"Sequence step error: {se}")
            return confirm

        elif t == "answer":
            return str(p)

        else:
            return str(p)

    except Exception as e:
        log(f"Action error: {e}")
        return f"Something went wrong, sir."


def _launch_task_in_claude(task: str):
    """Open VS Code, then open Claude Code terminal, then type the task."""
    # 1. Open VS Code
    subprocess.Popen(["open", "-a", "Visual Studio Code"])
    time.sleep(2.5)

    # 2. Open Terminal with Claude Code
    safe_task = task.replace('"', '\\"').replace("\n", " ")
    apple_script = f'''
    tell application "Terminal"
        activate
        do script "claude"
    end tell
    '''
    subprocess.Popen(["osascript", "-e", apple_script])
    time.sleep(4)  # wait for claude to start

    # 3. Type the task into the Terminal (frontmost window)
    type_script = f'''
    tell application "System Events"
        tell application "Terminal" to activate
        delay 0.5
        keystroke "{safe_task}"
        delay 0.3
        key code 36
    end tell
    '''
    subprocess.Popen(["osascript", "-e", type_script])


def _narrate_news(headlines: str) -> str:
    """Send headlines to Claude to narrate as JARVIS."""
    prompt = f"""You are JARVIS. Narrate these BBC news headlines to Vivaan in spoken English.
Be concise — pick the 3 most important stories and explain them in 4-5 sentences total.
No markdown. No bullets. Conversational, intelligent delivery. Start with "Here's what's happening in the world right now, sir."

Headlines:
{headlines}"""

    result = subprocess.run(
        [CLAUDE_BIN, "--print", "--no-session-persistence", prompt],
        capture_output=True, text=True, timeout=20
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return "I couldn't fetch the news just now, sir."


# ─── Claude Interpreter ───────────────────────────────────────

def interpret_command(command: str) -> dict:
    context      = build_context()
    days_left    = (BMW_DEADLINE - date.today()).days
    daily_target = BMW_TARGET / max(days_left, 1)
    has_news     = any(w in command for w in ["news", "world", "happening", "today", "latest", "headlines", "current events"])

    news_hint = ""
    if has_news:
        live = fetch_news(8)
        if live:
            news_hint = f"\n\nLIVE BBC NEWS HEADLINES (use these to answer news questions):\n{live}"

    prompt = f"""{context}{news_hint}

Voice command from Vivaan: "{command}"

Return ONLY a single valid JSON object. No explanation. No markdown. Just the JSON.

━━━ ACTION TYPES ━━━

Single actions:
  open_app         payload = exact macOS app name string (e.g. "Spotify", "Figma", "Google Chrome")
  open_url         payload = full URL string
  web_search       payload = search query string
  youtube_search   payload = search query string
  open_folder      payload = path string (~/ supported)
  volume_up        payload = null
  volume_down      payload = null
  volume_set       payload = integer 0-100
  mute             payload = null
  screenshot       payload = null
  lock             payload = null
  terminal_command payload = shell command string
  execute_task     payload = full task description to send to Claude Code
  news             payload = fallback answer string
  answer           payload = JARVIS spoken response string (no markdown, 2-4 sentences)

Multi-step sequence (use when task needs multiple apps or steps):
  sequence   payload = array of action objects (each has "type" and "payload")
             confirm = spoken confirmation string (what JARVIS says after sequence fires)
             Add "delay": seconds between steps where needed

━━━ INTELLIGENCE RULES ━━━

Think like Tony Stark's JARVIS — understand the REAL need, pick the SMARTEST tool:

1. CODING / BUILDING / DEV TASK → sequence: open VS Code + open Terminal with claude
   Example: "I need to build a website" or "code something" or "fix this bug"

2. DESIGN TASK (logo, UI, mockup, brand) → open Figma
   Example: "design a logo" / "create a UI" / "make a mockup"

3. AD CREATIVE / CANVA → open Canva (via Chrome URL)
   Example: "make an ad creative" / "design a post"

4. META ADS / FACEBOOK ADS → open Chrome to facebook.com/adsmanager
   Example: "open Meta ads" / "check my campaigns" / "run an ad"

5. MARKETING / CAMPAIGN TASK needing strategy → execute_task (Claude Code with Rohan context)
   Example: "plan my ad campaign" / "write ad copy" / "build a campaign"

6. CLIENT MEETING / CALL → open Zoom or Google Meet via Chrome
   Example: "start a meeting" / "join a call"

7. MUSIC / FOCUS → open Spotify
   Example: "play music" / "put on some music" / "open spotify"

8. EMAIL → open Chrome to gmail.com
   Example: "check my email" / "open gmail"

9. NOTE / WRITE SOMETHING → open Notion or Notes
   Example: "take a note" / "write this down" / "open notion"

10. NEWS / WORLD EVENTS → use "news" type (JARVIS narrates, never opens browser)

11. OPEN APP BY NAME → use open_app with exact app name

12. SYSTEM CONTROL → volume / screenshot / lock

━━━ EXAMPLES ━━━

"I need to build a landing page" →
{{"type":"sequence","payload":[{{"type":"open_app","payload":"Visual Studio Code"}},{{"type":"terminal_command","payload":"claude","delay":2}}],"confirm":"Opening VS Code and Claude Code for you, sir. Ready to build."}}

"I have a design task, need to make a logo" →
{{"type":"open_app","payload":"Figma"}}

"play some music" →
{{"type":"open_app","payload":"Spotify"}}

"open my Meta ads" →
{{"type":"open_url","payload":"https://www.facebook.com/adsmanager"}}

"I need to plan a campaign for my client" →
{{"type":"execute_task","payload":"Plan a full Meta ads campaign for my client. Use the 6-step system. Ask me for the product details."}}

"what's happening in the world" →
{{"type":"news","payload":"Here is what I know, sir..."}}

"take a screenshot" →
{{"type":"screenshot","payload":null}}

"how many days to my BMW" →
{{"type":"answer","payload":"You have {days_left} days remaining, sir. You need rupees {daily_target:,.0f} per day to hit your target."}}

"I need to write a proposal for a client" →
{{"type":"open_app","payload":"Notion"}}

"join a zoom call" →
{{"type":"open_app","payload":"Zoom"}}

"check my email" →
{{"type":"open_url","payload":"https://mail.google.com"}}

Now parse this command and return the smartest possible action:
"{command}"
"""

    result = subprocess.run(
        [CLAUDE_BIN, "--print", "--no-session-persistence", prompt],
        capture_output=True, text=True, timeout=25
    )

    if result.returncode != 0 or not result.stdout.strip():
        return {"type": "answer", "payload": "I couldn't reach my servers, sir."}

    raw = result.stdout.strip()
    try:
        start = raw.index("{")
        end   = raw.rindex("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {"type": "answer", "payload": raw[:400]}


# ─── Voice Pipeline ───────────────────────────────────────────

def listen_for_command(recognizer, mic) -> str:
    try:
        with mic as source:
            audio = recognizer.listen(source, timeout=2, phrase_time_limit=20)
        return recognizer.recognize_google(audio).lower()
    except (sr.WaitTimeoutError, sr.UnknownValueError):
        return ""
    except Exception as e:
        log(f"Listen error: {e}")
        return ""


def handle_command(command, recognizer, mic):
    log(f"Command: '{command}'")
    notify(f"Processing: {command[:60]}")
    action   = interpret_command(command)
    log(f"Action: {action.get('type')} — {str(action.get('payload',''))[:80]}")
    response = execute_action(action)
    log(f"Speaking: {response[:80]}")
    speak(response)
    play_sound("Pop")


# ─── Main Loop ────────────────────────────────────────────────

def run_jarvis():
    global _running

    recognizer = sr.Recognizer()
    recognizer.energy_threshold          = 3000
    recognizer.dynamic_energy_threshold  = True
    recognizer.pause_threshold           = 1.5
    recognizer.non_speaking_duration     = 1.0
    recognizer.phrase_threshold          = 0.3

    mic = sr.Microphone()

    log(f"Calibrating mic (mode={MODE})...")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)

    if MODE == "always":
        log("JARVIS always-on. Say 'stop' to deactivate.")
        speak("Always-on mode activated, sir.")
    else:
        log("JARVIS single-command mode.")
        speak("JARVIS ready, sir.")

    if MODE == "single":
        # Listen for one command, execute, done
        play_sound("Tink")
        speak("What can I do for you?")
        command = listen_for_command(recognizer, mic)
        if command and not any(s in command for s in STOP_WORDS):
            handle_command(command, recognizer, mic)
        else:
            speak("Understood. Standing by.")
        return

    # Always-on mode — background listener
    def background_callback(recognizer, audio):
        global _running
        try:
            text = recognizer.recognize_google(audio).lower().strip()
            log(f"Heard: '{text}'")

            # Stop command — kill speech and exit always-on
            if any(text == s or text.endswith(s) for s in STOP_WORDS):
                stop_speaking()
                speak("Standing by, sir.")
                _running = False
                return

            # Wake word check
            if any(w in text for w in WAKE_WORDS):
                play_sound("Tink")
                command = text
                for w in sorted(WAKE_WORDS, key=len, reverse=True):
                    command = command.replace(w, "").strip(" ,.")

                if not command or len(command) < 3:
                    speak("Sir?")
                    command = listen_for_command(recognizer, mic)

                if command and len(command) >= 3:
                    # Check again for stop in follow-up
                    if any(s in command for s in STOP_WORDS):
                        stop_speaking()
                        speak("Standing by, sir.")
                        _running = False
                        return
                    threading.Thread(
                        target=handle_command,
                        args=(command, recognizer, mic),
                        daemon=True
                    ).start()
                else:
                    speak("I didn't catch that, sir.")

        except sr.UnknownValueError:
            pass
        except Exception as e:
            log(f"Callback error: {e}")

    stop_fn = recognizer.listen_in_background(mic, background_callback, phrase_time_limit=20)

    try:
        while _running:
            time.sleep(0.3)
    except KeyboardInterrupt:
        pass
    finally:
        stop_fn(wait_for_stop=False)
        log("JARVIS offline.")
        stop_speaking()


if __name__ == "__main__":
    run_jarvis()

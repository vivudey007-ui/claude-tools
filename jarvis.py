#!/usr/bin/env python3
"""
JARVIS — Full voice computer agent for Vivaan
Say "Jarvis" → speak command → JARVIS controls the Mac

Supports: open apps, open URLs, web search, system controls,
          run terminal commands, answer questions, file operations.
"""

import speech_recognition as sr
import subprocess
import sys
import time
import threading
import json
import os
from datetime import datetime, date

CLAUDE_BIN = "/Users/vivaandey/.local/bin/claude"
VOICE = "Daniel"
SPEECH_RATE = 190

BMW_TARGET = 5000000
BMW_DEADLINE = date(2027, 3, 9)

WAKE_WORDS = ["jarvis", "hey jarvis", "yo jarvis", "okay jarvis", "ok jarvis"]

SOUND_WAKE = "Tink"
SOUND_DONE = "Pop"
SOUND_ERROR = "Basso"


# ─── Utilities ────────────────────────────────────────────────

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def play_sound(name):
    subprocess.Popen(["afplay", f"/System/Library/Sounds/{name}.aiff"])


def speak(text):
    clean = (text
        .replace("**", "").replace("*", "")
        .replace("`", "").replace("#", "")
        .replace('"', "").replace("—", ","))
    subprocess.run(["say", "-v", VOICE, "-r", str(SPEECH_RATE), clean])


def notify(title, msg):
    subprocess.Popen([
        "osascript", "-e",
        f'display notification "{msg}" with title "{title}"'
    ])


# ─── Action Executor ──────────────────────────────────────────

def execute_action(action: dict) -> str:
    """
    Execute a parsed JARVIS action. Returns confirmation string to speak.
    Action schema: { "type": str, "payload": any }
    """
    t = action.get("type", "answer")
    p = action.get("payload", "")

    try:

        if t == "open_app":
            subprocess.Popen(["open", "-a", p])
            return f"Opening {p}, sir."

        elif t == "open_url":
            subprocess.Popen(["open", p])
            return f"Opening that for you now, sir."

        elif t == "web_search":
            query = p.replace(" ", "+")
            subprocess.Popen(["open", f"https://www.google.com/search?q={query}"])
            return f"Searching for {p}."

        elif t == "youtube_search":
            query = p.replace(" ", "+")
            subprocess.Popen(["open", f"https://www.youtube.com/results?search_query={query}"])
            return f"Pulling up {p} on YouTube."

        elif t == "open_folder":
            path = os.path.expanduser(p)
            subprocess.Popen(["open", path])
            return f"Opening {p}."

        elif t == "open_file":
            path = os.path.expanduser(p)
            subprocess.Popen(["open", path])
            return f"Opening that file, sir."

        elif t == "system":
            cmd = p.get("cmd") if isinstance(p, dict) else p
            # Safety: block destructive commands
            blocked = ["rm ", "sudo rm", "format", "mkfs", "> /dev", "dd if"]
            if any(b in cmd for b in blocked):
                return "I won't run that command, sir. Too destructive."
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            out = result.stdout.strip() or result.stderr.strip()
            return p.get("confirm", "Done.") if isinstance(p, dict) else (out[:200] if out else "Done, sir.")

        elif t == "volume":
            level = int(p)
            subprocess.run(["osascript", "-e", f"set volume output volume {level}"])
            return f"Volume set to {level} percent."

        elif t == "volume_up":
            subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) + 10)"])
            return "Volume up."

        elif t == "volume_down":
            subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) - 10)"])
            return "Volume down."

        elif t == "mute":
            subprocess.run(["osascript", "-e", "set volume with output muted"])
            return "Muted."

        elif t == "screenshot":
            path = f"/Users/vivaandey/Desktop/screenshot_{datetime.now().strftime('%H%M%S')}.png"
            subprocess.run(["screencapture", "-x", path])
            subprocess.Popen(["open", path])
            return f"Screenshot saved to Desktop."

        elif t == "show_desktop":
            subprocess.run(["osascript", "-e", 'tell application "Finder" to set desktop picture to POSIX file "/System/Library/Desktop Pictures/Sequoia.heic"'])
            return "Showing desktop."

        elif t == "lock":
            subprocess.run(["pmset", "displaysleepnow"])
            return "Locking screen, sir."

        elif t == "terminal_command":
            cmd = p
            blocked = ["rm -rf", "sudo rm", "mkfs", "dd if="]
            if any(b in cmd for b in blocked):
                return "Blocked — too destructive, sir."
            safe_cmd = cmd.replace('"', '\\"')
            apple_script = f'''
            tell application "Terminal"
                activate
                do script "{safe_cmd}"
            end tell
            '''
            subprocess.Popen(["osascript", "-e", apple_script])
            return f"Running that in Terminal."

        elif t == "open_claude":
            subprocess.Popen(["open", "-a", "Claude"])
            return "Opening Claude."

        elif t == "answer":
            return str(p)

        elif t == "unknown":
            return "I didn't quite catch that, sir. Could you rephrase?"

        else:
            return str(p)

    except Exception as e:
        log(f"Action error: {e}")
        return f"Something went wrong, sir: {str(e)[:80]}"


# ─── Claude Command Interpreter ───────────────────────────────

def get_jarvis_context():
    days_left = (BMW_DEADLINE - date.today()).days
    daily_target = BMW_TARGET / max(days_left, 1)
    hour = datetime.now().hour
    tod = "morning" if hour < 12 else ("afternoon" if hour < 18 else "evening")

    log_path = f"/Users/vivaandey/.claude/daily-log/{date.today().isoformat()}.md"
    try:
        with open(log_path) as f:
            today_log = f.read()[:600]
    except FileNotFoundError:
        today_log = "No log yet today."

    return tod, days_left, daily_target, today_log


def interpret_command(command: str) -> dict:
    """
    Send command to Claude. Claude returns JSON action.
    """
    tod, days_left, daily_target, today_log = get_jarvis_context()

    prompt = f"""You are JARVIS, Vivaan's voice-controlled Mac assistant.
Parse his voice command and return a JSON action to execute.

Vivaan's context:
- Date: {date.today().strftime('%B %d, %Y')}, {tod}
- BMW goal: ₹50L by March 9, 2027 ({days_left} days, ₹{daily_target:,.0f}/day needed)
- Projects: DEY Marketing agency, deymarketing.in website
- Mac apps installed: Chrome, Safari, Terminal, VS Code, Spotify, Slack, WhatsApp, Finder, Notes, Calendar, Notion, Figma, Claude

Voice command: "{command}"

Return ONLY valid JSON. No explanation. No markdown. Just the JSON object.

Action types and when to use them:
- open_app: open a Mac application. payload = app name string (e.g. "Google Chrome", "Spotify", "VS Code")
- open_url: open a specific URL. payload = full URL string
- web_search: search Google. payload = search query string
- youtube_search: search YouTube. payload = search query string
- open_folder: open a folder in Finder. payload = path string (e.g. "~/Desktop", "~/Downloads")
- open_file: open a specific file. payload = file path string
- volume: set volume to specific level. payload = number 0-100
- volume_up: turn volume up. payload = null
- volume_down: turn volume down. payload = null
- mute: mute audio. payload = null
- screenshot: take screenshot. payload = null
- lock: lock/sleep the screen. payload = null
- terminal_command: run a shell command in Terminal window. payload = shell command string
- open_claude: open Claude app. payload = null
- answer: answer a question or have a conversation. payload = your response as JARVIS (British, precise, 2-3 sentences max, no markdown)
- unknown: can't parse the command. payload = null

Examples:
"open spotify" → {{"type": "open_app", "payload": "Spotify"}}
"search youtube for lo-fi beats" → {{"type": "youtube_search", "payload": "lo-fi beats"}}
"turn the volume down" → {{"type": "volume_down", "payload": null}}
"open my downloads" → {{"type": "open_folder", "payload": "~/Downloads"}}
"what's my BMW goal" → {{"type": "answer", "payload": "You need ₹{daily_target:,.0f} per day to hit your target. {days_left} days remaining, sir."}}
"run git status" → {{"type": "terminal_command", "payload": "git status"}}
"take a screenshot" → {{"type": "screenshot", "payload": null}}
"open chrome and go to youtube" → {{"type": "open_url", "payload": "https://www.youtube.com"}}
"what's going on today" → {{"type": "answer", "payload": "Good {tod}, Vivaan. Today's log: {today_log[:100]}..."}}

Now parse: "{command}"
"""

    result = subprocess.run(
        [CLAUDE_BIN, "--print", "--no-session-persistence", prompt],
        capture_output=True,
        text=True,
        timeout=20
    )

    if result.returncode != 0 or not result.stdout.strip():
        return {"type": "answer", "payload": "I couldn't reach the servers, sir."}

    raw = result.stdout.strip()

    # Extract JSON from response
    try:
        # Find first { and last }
        start = raw.index("{")
        end = raw.rindex("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        log(f"JSON parse failed: {raw[:100]}")
        return {"type": "answer", "payload": raw[:300]}


# ─── Voice Listener ───────────────────────────────────────────

def listen_for_command(recognizer, mic):
    """Listen up to 8 seconds for the full command after wake word."""
    try:
        with mic as source:
            audio = recognizer.listen(source, timeout=1.5, phrase_time_limit=8)
        return recognizer.recognize_google(audio).lower()
    except (sr.WaitTimeoutError, sr.UnknownValueError):
        return ""
    except Exception as e:
        log(f"Listen error: {e}")
        return ""


def handle_command(command, recognizer, mic):
    """Full pipeline: command → interpret → execute → speak."""
    log(f"Command: '{command}'")
    notify("JARVIS", f"Processing: {command}")

    action = interpret_command(command)
    log(f"Action: {action}")

    response = execute_action(action)
    log(f"Response: {response}")

    speak(response)
    play_sound(SOUND_DONE)


def run_jarvis():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 3000
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8

    mic = sr.Microphone()
    pending_double = [None]

    log("Calibrating mic...")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)
    log("JARVIS online. Listening for wake word...")
    speak("JARVIS online, sir. Ready.")

    def background_callback(recognizer, audio):
        try:
            text = recognizer.recognize_google(audio).lower()
            log(f"Heard: '{text}'")

            if any(w in text for w in WAKE_WORDS):
                play_sound(SOUND_WAKE)

                # Strip wake word, keep the command if said in same sentence
                command = text
                for w in sorted(WAKE_WORDS, key=len, reverse=True):
                    command = command.replace(w, "").strip(" ,.")

                # If no command in same utterance, listen for follow-up
                if not command or len(command) < 3:
                    speak("Sir?")
                    command = listen_for_command(recognizer, mic)

                if command and len(command) >= 3:
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
            log(f"Error: {e}")

    stop_listening = recognizer.listen_in_background(mic, background_callback, phrase_time_limit=10)

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop_listening(wait_for_stop=False)
        log("JARVIS offline.")
        speak("Going offline, sir.")


if __name__ == "__main__":
    run_jarvis()

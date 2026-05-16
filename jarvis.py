#!/usr/bin/env python3
"""
JARVIS — Vivaan's always-on voice assistant
Say "Jarvis" → JARVIS listens for command → Claude responds → Daniel speaks

Wake phrases detected: "jarvis", "hey jarvis", "yo jarvis"
"""

import speech_recognition as sr
import subprocess
import sys
import time
import threading
from datetime import datetime, date

CLAUDE_BIN = "/Users/vivaandey/.local/bin/claude"
VOICE = "Daniel"
SPEECH_RATE = 190

BMW_TARGET = 5000000
BMW_DEADLINE = date(2027, 3, 9)

WAKE_WORDS = ["jarvis", "hey jarvis", "yo jarvis", "okay jarvis"]

# Earcon sounds (macOS system sounds)
SOUND_WAKE = "Tink"       # Jarvis heard wake word
SOUND_DONE = "Pop"        # Response done


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def play_sound(name):
    subprocess.Popen(["afplay", f"/System/Library/Sounds/{name}.aiff"])


def speak(text):
    clean = text.replace("**", "").replace("*", "").replace("`", "").replace("#", "")
    subprocess.run(["say", "-v", VOICE, "-r", str(SPEECH_RATE), clean])
    play_sound(SOUND_DONE)


def get_context():
    days_left = (BMW_DEADLINE - date.today()).days
    daily_target = BMW_TARGET / max(days_left, 1)
    hour = datetime.now().hour
    if hour < 12:
        tod = "morning"
    elif hour < 18:
        tod = "afternoon"
    else:
        tod = "evening"

    # Read today's log if it exists
    log_path = f"/Users/vivaandey/.claude/daily-log/{date.today().isoformat()}.md"
    try:
        with open(log_path) as f:
            today_log = f.read()[:800]
    except FileNotFoundError:
        today_log = "No log yet today."

    return f"""You are JARVIS — Vivaan's personal AI assistant. Think Tony Stark's JARVIS.

Identity rules:
- British, precise, confident. Never waffle.
- Call him "sir" or "Vivaan" — never "buddy", "man", or "bro"
- You are intelligent, slightly dry, always competent
- Short answers unless detail is clearly needed
- No filler words. No "of course" or "certainly". Direct delivery.
- When giving status updates, lead with the most important thing first

Current context:
- Time of day: {tod}
- Today's date: {date.today().strftime('%B %d, %Y')}
- BMW Goal: ₹50,00,000 by March 9, 2027 ({days_left} days remaining)
- Required daily average: ₹{daily_target:,.0f}/day
- Active projects: DEY Marketing (agency), deymarketing.in (website)
- Agents available: Arya (web design), Rohan (Meta ads)

Today's log:
{today_log}

Respond in 2-4 sentences max. Spoken aloud — no markdown, no bullets, no formatting.
"""


def ask_jarvis(command: str) -> str:
    context = get_context()
    prompt = f"{context}\n\nVivaan just said: \"{command}\"\n\nRespond as JARVIS."

    result = subprocess.run(
        [CLAUDE_BIN, "--print", "--no-session-persistence", prompt],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return "Apologies, sir. I couldn't reach the servers."


def listen_for_command(recognizer: sr.Recognizer, mic: sr.Microphone) -> str:
    """Listen for up to 6 seconds after wake word for the full command."""
    log("Listening for command...")
    try:
        with mic as source:
            audio = recognizer.listen(source, timeout=1, phrase_time_limit=8)
        return recognizer.recognize_google(audio).lower()
    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        log(f"Command listen error: {e}")
        return ""


def run_jarvis():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 3000
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8

    mic = sr.Microphone()

    # Calibrate
    log("Calibrating mic...")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)
    log("JARVIS online. Listening for wake word...")
    speak("JARVIS online, sir.")

    def background_callback(recognizer, audio):
        try:
            text = recognizer.recognize_google(audio).lower()
            log(f"Heard: '{text}'")

            # Check for wake word
            if any(w in text for w in WAKE_WORDS):
                play_sound(SOUND_WAKE)
                log("Wake word detected — listening for command...")

                # Extract command from same utterance (e.g. "Jarvis what's going on")
                command = text
                for w in WAKE_WORDS:
                    command = command.replace(w, "").strip()

                # If command was just the wake word, listen for follow-up
                if not command or len(command) < 4:
                    command = listen_for_command(recognizer, mic)

                if command:
                    log(f"Command: '{command}'")
                    response = ask_jarvis(command)
                    log(f"JARVIS: {response}")
                    speak(response)
                else:
                    speak("Yes, sir? I didn't catch that.")

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

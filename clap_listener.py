#!/usr/bin/env python3
"""
Clap Wake - Multi-clap detector for Vivaan
  2 claps → Voice Agent (screenshot → OCR → Claude → speak)
  3 claps → Daily Briefing (opens Terminal window)
"""

import sounddevice as sd
import numpy as np
import time
import subprocess
import sys
import os
from datetime import datetime

# --- Config ---
SAMPLE_RATE = 44100
BLOCK_SIZE = 1024
CLAP_THRESHOLD = 0.3        # Volume level to count as clap (0.0 - 1.0)
DOUBLE_CLAP_WINDOW = 0.8    # Max seconds between 2 claps
TRIPLE_CLAP_WINDOW = 1.5    # Max seconds for 3 claps
MIN_GAP = 0.15              # Min seconds between claps (avoid false doubles)
COOLDOWN = 5.0              # Seconds to ignore after trigger (prevent re-fire)
TRIPLE_WAIT = 0.5           # Wait this long after 2nd clap before firing, to allow a 3rd

CLAUDE_BIN = "/Users/vivaandey/.local/bin/claude"
BRIEFING_SCRIPT = "/Users/vivaandey/.claude/tools/briefing.py"
VOICE_SCRIPT = "/Users/vivaandey/.claude/tools/voice_agent.py"

# --- State ---
clap_times = []
last_trigger = 0.0
pending_double = None        # Timer thread waiting to confirm no 3rd clap

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def trigger_voice_agent():
    """2 claps — read screen and speak explanation."""
    global last_trigger
    last_trigger = time.time()
    log("Double clap → Voice Agent")
    subprocess.Popen([sys.executable, VOICE_SCRIPT])

def trigger_briefing():
    """3 claps — open full daily briefing in Terminal."""
    global last_trigger
    last_trigger = time.time()
    log("Triple clap → Daily Briefing")

    subprocess.Popen([
        "osascript", "-e",
        'display notification "Launching daily briefing..." with title "Clap Wake 👋"'
    ])

    apple_script = '''
    tell application "Terminal"
        activate
        do script "python3 /Users/vivaandey/.claude/tools/briefing.py"
    end tell
    '''
    subprocess.Popen(["osascript", "-e", apple_script])

def audio_callback(indata, frames, time_info, status):
    global clap_times, last_trigger, pending_double

    now = time.time()

    if now - last_trigger < COOLDOWN:
        return

    volume = float(np.max(np.abs(indata)))

    if volume > CLAP_THRESHOLD:
        clap_times = [t for t in clap_times if now - t < TRIPLE_CLAP_WINDOW]

        if clap_times and (now - clap_times[-1]) < MIN_GAP:
            return

        clap_times.append(now)
        count = len(clap_times)
        log(f"Clap detected (vol={volume:.2f}) — {count} in window")

        if count == 3:
            # Cancel pending double, fire triple
            if pending_double:
                pending_double.cancel()
            clap_times = []
            import threading
            threading.Thread(target=trigger_briefing, daemon=True).start()

        elif count == 2:
            # Wait TRIPLE_WAIT seconds — if no 3rd clap arrives, fire voice agent
            import threading
            if pending_double:
                pending_double.cancel()
            def fire_double():
                global pending_double
                pending_double = None
                if len(clap_times) < 3:
                    clap_times.clear()
                    trigger_voice_agent()
            t = threading.Timer(TRIPLE_WAIT, fire_double)
            pending_double = t
            t.start()

def main():
    log("Clap Wake started.")
    log("  2 claps → Voice Agent (read screen aloud)")
    log("  3 claps → Daily Briefing")
    log(f"  Threshold: {CLAP_THRESHOLD} | Window: {DOUBLE_CLAP_WINDOW}s")

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            channels=1,
            dtype='float32',
            callback=audio_callback
        ):
            log("Mic active. Double-clap to wake Claude.")
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        log("Stopped.")
    except Exception as e:
        log(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

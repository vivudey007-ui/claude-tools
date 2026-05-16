#!/usr/bin/env python3
"""
Clap Wake - Double clap detector for Vivaan
Listens for 2 claps within 0.8s → triggers Claude briefing
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
MIN_GAP = 0.15              # Min seconds between claps (avoid false doubles)
COOLDOWN = 5.0              # Seconds to ignore after trigger (prevent re-fire)

CLAUDE_BIN = "/Users/vivaandey/.local/bin/claude"
BRIEFING_SCRIPT = "/Users/vivaandey/.claude/tools/briefing.py"

# --- State ---
clap_times = []
last_trigger = 0.0

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def trigger_briefing():
    global last_trigger
    last_trigger = time.time()
    log("Double clap detected! Launching Claude briefing...")

    # macOS notification
    subprocess.Popen([
        "osascript", "-e",
        'display notification "Launching Claude briefing..." with title "Clap Wake 👋"'
    ])

    # Launch briefing in new terminal window
    apple_script = '''
    tell application "Terminal"
        activate
        do script "python3 /Users/vivaandey/.claude/tools/briefing.py"
    end tell
    '''
    subprocess.Popen(["osascript", "-e", apple_script])

def audio_callback(indata, frames, time_info, status):
    global clap_times, last_trigger

    now = time.time()

    # Skip if in cooldown
    if now - last_trigger < COOLDOWN:
        return

    # Get peak volume of this block
    volume = float(np.max(np.abs(indata)))

    if volume > CLAP_THRESHOLD:
        # Remove old clap times outside window
        clap_times = [t for t in clap_times if now - t < DOUBLE_CLAP_WINDOW]

        # Check gap from last clap
        if clap_times and (now - clap_times[-1]) < MIN_GAP:
            return  # Too fast, same clap still ringing

        clap_times.append(now)
        log(f"Clap detected (vol={volume:.2f}) — {len(clap_times)} in window")

        if len(clap_times) >= 2:
            clap_times = []
            trigger_briefing()

def main():
    log("Clap Wake started. Listening for double clap...")
    log(f"Threshold: {CLAP_THRESHOLD} | Window: {DOUBLE_CLAP_WINDOW}s")

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

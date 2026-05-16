#!/usr/bin/env python3
"""
Clap Wake - Multi-clap detector for Vivaan
  2 claps → Voice Agent (screenshot → OCR → JARVIS reads screen aloud)
  3 claps → JARVIS single command (listen once, execute, done)
  4 claps → JARVIS always-on (stays active until you say "stop")
"""

import sounddevice as sd
import numpy as np
import time
import subprocess
import sys
import os
import threading
from datetime import datetime

# --- Config ---
SAMPLE_RATE       = 44100
BLOCK_SIZE        = 1024
CLAP_THRESHOLD    = 0.3     # 0.0-1.0 — lower = more sensitive
CLAP_WINDOW       = 2.0     # seconds to collect all claps in a sequence
MIN_GAP           = 0.15    # min gap between claps (prevent double-count)
COOLDOWN          = 6.0     # ignore period after trigger fires
SETTLE_WAIT       = 0.6     # wait after last clap before deciding count

VOICE_SCRIPT      = "/Users/vivaandey/.claude/tools/voice_agent.py"
JARVIS_SCRIPT     = "/Users/vivaandey/.claude/tools/jarvis.py"

# --- State ---
clap_times    = []
last_trigger  = 0.0
settle_timer  = None
_jarvis_proc  = None   # track always-on JARVIS process


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def notify(msg):
    subprocess.Popen(["osascript", "-e",
        f'display notification "{msg}" with title "Clap Wake"'])


def kill_jarvis():
    global _jarvis_proc
    if _jarvis_proc and _jarvis_proc.poll() is None:
        _jarvis_proc.terminate()
        _jarvis_proc = None
        log("JARVIS always-on killed.")


def trigger_voice_agent():
    global last_trigger
    last_trigger = time.time()
    log("2 claps → Voice Agent (screen read)")
    notify("Reading screen...")
    subprocess.Popen([sys.executable, VOICE_SCRIPT])


def trigger_jarvis_single():
    global last_trigger
    last_trigger = time.time()
    log("3 claps → JARVIS single command")
    notify("JARVIS listening...")
    subprocess.Popen([sys.executable, JARVIS_SCRIPT, "--single"])


def trigger_jarvis_always():
    global last_trigger, _jarvis_proc
    last_trigger = time.time()

    # Kill existing always-on instance if running
    kill_jarvis()

    log("4 claps → JARVIS always-on")
    notify("JARVIS always-on activated")
    _jarvis_proc = subprocess.Popen([sys.executable, JARVIS_SCRIPT, "--always"])


def fire_sequence(count):
    """Called after settle_wait — decide what to trigger based on clap count."""
    global clap_times
    clap_times = []
    log(f"Sequence complete: {count} clap(s)")

    if count == 2:
        trigger_voice_agent()
    elif count == 3:
        trigger_jarvis_single()
    elif count >= 4:
        trigger_jarvis_always()
    # 1 clap = ignore


def audio_callback(indata, frames, time_info, status):
    global clap_times, last_trigger, settle_timer

    now = time.time()

    if now - last_trigger < COOLDOWN:
        return

    volume = float(np.max(np.abs(indata)))

    if volume > CLAP_THRESHOLD:
        # Drop claps outside the collection window
        clap_times = [t for t in clap_times if now - t < CLAP_WINDOW]

        # Debounce — same clap still ringing
        if clap_times and (now - clap_times[-1]) < MIN_GAP:
            return

        clap_times.append(now)
        count = len(clap_times)
        log(f"Clap {count} (vol={volume:.2f})")

        # Reset settle timer — wait for more claps
        if settle_timer:
            settle_timer.cancel()
        t = threading.Timer(SETTLE_WAIT, fire_sequence, args=(count,))
        settle_timer = t
        t.start()


def main():
    log("Clap Wake started.")
    log("  2 claps → JARVIS reads screen aloud")
    log("  3 claps → JARVIS single command mode")
    log("  4 claps → JARVIS always-on mode")
    log(f"  Threshold: {CLAP_THRESHOLD} | Window: {CLAP_WINDOW}s")

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            channels=1,
            dtype='float32',
            callback=audio_callback
        ):
            log("Mic active.")
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        log("Stopped.")
        kill_jarvis()
    except Exception as e:
        log(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

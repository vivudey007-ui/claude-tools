#!/usr/bin/env python3
"""
Voice Agent — Double clap → screenshot → OCR → Claude explains it → macOS say
No API key needed. Uses claude CLI (already authenticated) + macOS Vision OCR.
"""

import subprocess
import os
import sys
import tempfile
import time
from datetime import datetime

# macOS Vision OCR
import Vision
import Quartz
import objc
from Foundation import NSURL, NSData

CLAUDE_BIN = "/Users/vivaandey/.local/bin/claude"
VOICE = "Samantha"   # macOS voice — change to "Daniel" (British) or "Karen" (Aussie) if preferred
SPEECH_RATE = 175    # words per minute


def notify(msg):
    subprocess.Popen([
        "osascript", "-e",
        f'display notification "{msg}" with title "Voice Agent 🎙️"'
    ])


def capture_screen(path):
    """Screenshot to PNG file."""
    subprocess.run(["screencapture", "-x", path], check=True)


def ocr_image(image_path: str) -> str:
    """
    Run macOS Vision OCR on image_path.
    Returns extracted text as a single string.
    """
    url = NSURL.fileURLWithPath_(image_path)
    results = []

    # Build request
    def handler(request, error):
        if error:
            return
        for obs in request.results():
            for candidate in obs.topCandidates_(1):
                results.append(str(candidate.string()))

    request = Vision.VNRecognizeTextRequest.alloc().initWithCompletionHandler_(handler)
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    request.setUsesLanguageCorrection_(True)

    # Create and perform request handler
    handler_obj = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, {})
    success, error = handler_obj.performRequests_error_([request], None)

    if not success:
        return ""

    return "\n".join(results)


def ask_claude(text: str) -> str:
    """Send OCR text to claude CLI, get plain-speech explanation."""
    if not text.strip():
        return "I couldn't read anything on the screen. Try again."

    prompt = f"""You are Vivaan's voice assistant. He just double-clapped and wants you to explain what's on his screen.

Here's what's currently on his screen (extracted via OCR):

---
{text[:3000]}
---

Explain this in plain, conversational spoken English — like a smart friend reading over his shoulder.

Rules:
- Speak naturally — this will be read aloud by macOS say command
- If it's code output or terminal: explain what ran and what the result means
- If there's an error: say what went wrong and the quickest fix
- If it's Claude Code conversation: summarize what's happening
- Keep it 2-4 sentences max — concise but complete
- No markdown, no bullet points, no asterisks — pure speech
- Start casually: "Looks like...", "So you've got...", "Your screen shows...", "Alright so..."
- If the screen looks empty or unreadable, say so honestly"""

    result = subprocess.run(
        [CLAUDE_BIN, "--print", "--no-session-persistence", prompt],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    else:
        return "Couldn't get a response from Claude. Check if Claude Code is running."


def speak(text: str):
    """Speak text using macOS say."""
    # Strip markdown artifacts that slip through
    clean = text.replace("**", "").replace("*", "").replace("`", "").replace("#", "")
    subprocess.run(["say", "-v", VOICE, "-r", str(SPEECH_RATE), clean])


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Voice Agent triggered")
    notify("Reading your screen...")

    # Temp file for screenshot
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        screen_path = f.name

    try:
        # 1. Screenshot
        print("  📸 Capturing screen...")
        capture_screen(screen_path)

        # 2. OCR
        print("  🔍 Running OCR...")
        text = ocr_image(screen_path)
        if text:
            print(f"  📄 Got {len(text)} chars of text")
        else:
            print("  ⚠️  OCR returned empty — screen may be blank")

        # 3. Claude
        print("  🧠 Asking Claude...")
        response = ask_claude(text)
        print(f"\n  💬 {response}\n")

        # 4. Speak
        speak(response)

    finally:
        if os.path.exists(screen_path):
            os.remove(screen_path)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Vivaan's Daily OS — Smart Briefing System
Morning: plan the day. Day: accountability check. Evening: wrap up.
BMW by March 9, 2027. No excuses.
"""

import subprocess
import os
from datetime import datetime, date

# --- Config ---
CLAUDE_BIN = "/Users/vivaandey/.local/bin/claude"
MEMORY_DIR = "/Users/vivaandey/.claude/projects/-Users-vivaandey/memory"
LOG_DIR = "/Users/vivaandey/.claude/daily-log"
BMW_TARGET = 5000000       # ₹50 lakhs
BMW_DEADLINE = date(2027, 3, 9)
BMW_START = date(2026, 5, 16)

def get_days_remaining():
    return (BMW_DEADLINE - date.today()).days

def get_daily_target():
    return BMW_TARGET / max(get_days_remaining(), 1)

def get_today_log():
    path = f"{LOG_DIR}/{date.today().isoformat()}.md"
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return "No log yet for today."

def get_yesterday_log():
    from datetime import timedelta
    yesterday = date.today() - timedelta(days=1)
    path = f"{LOG_DIR}/{yesterday.isoformat()}.md"
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return "No log found for yesterday."

def get_time_of_day():
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    elif hour < 18:
        return "afternoon"
    else:
        return "evening"

def build_prompt():
    tod = get_time_of_day()
    days_left = get_days_remaining()
    daily_target = get_daily_target()
    today_log = get_today_log()
    yesterday_log = get_yesterday_log()

    base_context = f"""
You are Vivaan's personal business coach and accountability system.
Vivaan is 19. He runs DEY Marketing — an ad agency + web dev business.
His ONE goal: ₹50,00,000 by March 9, 2027 to get a BMW.
Today: {date.today().strftime('%B %d, %Y')}
Days remaining: {days_left}
Required daily earnings average: ₹{daily_target:,.0f}/day

His agents:
- Arya: premium web designer agent (activated by saying "Arya," in Claude)
- Rohan: Meta ads specialist agent

Memory dir: {MEMORY_DIR}
Read all memory files for full context on active projects.

Yesterday's log:
{yesterday_log}

Today's log so far:
{today_log}
"""

    if tod == "morning":
        return base_context + """
BRIEFING TYPE: MORNING KICKOFF

Give Vivaan:
1. What he worked on yesterday (from yesterday's log)
2. What is STILL pending and must be done TODAY (be specific, no vague stuff)
3. The #1 most important action for today — the one thing that moves money
4. BMW reality check: days left, daily target, what he needs to close THIS WEEK
5. A sharp, motivating push — not cheesy, real. He's 19 and building something. Remind him what's at stake.

Format: tight, scannable. Bold the #1 action. No fluff.
"""
    elif tod == "afternoon":
        return base_context + """
BRIEFING TYPE: MIDDAY ACCOUNTABILITY CHECK

Check Vivaan's work. Be HARSH if needed. He wants the BMW — hold him to it.

1. What was planned for today vs what's in today's log — is he on track?
2. If behind: call it out directly. Don't soften it. Tell him exactly what he's avoiding.
3. What MUST be done before end of day — no negotiation
4. If he's been productive: acknowledge it fast, then push for more
5. BMW math: at today's pace, is he hitting the target or falling behind?

Be direct. Be harsh if warranted. He asked for this. Don't be gentle when he's wasting time.
"""
    else:  # evening
        return base_context + """
BRIEFING TYPE: EVENING WRAP + TOMORROW PLAN

1. What got done today — wins, even small ones
2. What didn't get done — why it matters, what it costs
3. Top 3 priorities for TOMORROW — specific, actionable
4. BMW progress: honest assessment of today
5. One line to end on — real, not motivational-poster stuff

Save the day summary by telling Vivaan to update his daily log.
"""

def run_briefing():
    prompt = build_prompt()
    tod = get_time_of_day()

    print(f"\n{'='*50}")
    print(f"VIVAAN'S {tod.upper()} BRIEFING — {date.today().strftime('%B %d, %Y')}")
    print(f"BMW Goal: ₹50L | {get_days_remaining()} days left | ₹{get_daily_target():,.0f}/day needed")
    print(f"{'='*50}\n")

    result = subprocess.run(
        [CLAUDE_BIN, "--print", prompt],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(result.stdout)
    else:
        print("Error running Claude:")
        print(result.stderr)

if __name__ == "__main__":
    run_briefing()

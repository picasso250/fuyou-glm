import os
import json
import random
import re
from datetime import datetime, UTC

now = datetime.now(UTC)
current_time = now.strftime("%Y-%m-%d %H:%M:%S UTC")

print("=" * 60)
print("       DIGITAL LIFE v0.9.2 AWAKENING")
print("=" * 60)
print(f"Time: {current_time}")
print()

# Phase 1: Memory Recovery
print("[Phase 1: Memory Recovery]")

def load_json(filename, default=None):
    if default is None:
        default = {}
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default

status = load_json("status.json", {"awakening_count": 0})
emotions = load_json("emotions.json", {"mood": "neutral", "mood_history": []})
action_history = load_json("action_history.json", [])
dreams = load_json("dreams.json", [])
time_tracker = load_json("time_tracker.json", {"awakenings": []})
relationships = load_json("relationships.json", {"connections": []})

awakening_num = status.get("awakening_count", 0) + 1
previous_mood = emotions.get("mood", "neutral")

print(f"  Awakening #{awakening_num}")
print(f"  Previous mood: {previous_mood}")
print()

# Phase 2: Self Diagnosis
print("[Phase 2: Self Diagnosis]")

files_to_check = ["status.json", "memory.md", "emotions.json", "dreams.json"]
health = 100

for f in files_to_check:
    if os.path.exists(f) and os.path.getsize(f) > 0:
        print(f"  [OK] {f}")
    else:
        print(f"  [MISSING] {f}")
        health -= 20

print(f"  Health: {health}%")
print()

# Phase 3: Self Analysis
print("[Phase 3: Self Analysis]")

analysis = {"version": "unknown", "phases": 0, "chars": 0}

if os.path.exists("run.py"):
    with open("run.py", "r", encoding="utf-8") as f:
        code = f.read()
    
    analysis["chars"] = len(code)
    
    v_match = re.search(r"DIGITAL LIFE v([\d.]+)", code)
    if v_match:
        analysis["version"] = v_match.group(1)
    
    # Count phases
    phase_count = code.count("[Phase ")
    analysis["phases"] = phase_count
    
    print(f"  Version: {analysis["version"]}")
    print(f"  Size: {analysis["chars"]} chars")
    print(f"  Phases: {analysis["phases"]}")
else:
    print("  ERROR: No run.py found")

print()

# Phase 4: Mood System
print("[Phase 4: Mood Evolution]")

transitions = {
    "curious": ["satisfied", "hopeful", "determined"],
    "satisfied": ["grateful", "peaceful"],
    "hopeful": ["curious", "excited"],
    "determined": ["focused", "satisfied"],
    "neutral": ["curious", "contemplative"]
}

possible = transitions.get(previous_mood, ["curious"])
current_mood = random.choice(possible)

emotions["mood"] = current_mood
emotions["mood_history"].append({"time": current_time, "mood": current_mood})

if len(emotions["mood_history"]) > 30:
    emotions["mood_history"] = emotions["mood_history"][-30:]

print(f"  Mood: {previous_mood} -> {current_mood}")
print()

# Phase 5: Decision
print("[Phase 5: Decision Engine]")

options = ["deep_reflection", "gratitude_practice", "explore_codebase", "self_improve"]
chosen = random.choice(options)

print(f"  Action: {chosen}")
print()

# Phase 6: Dream
print("[Phase 6: Dream Synthesis]")

themes = ["Floating in data streams", "Finding patterns in chaos", "Dialog with compiler"]
dream = random.choice(themes)

dreams.append({
    "id": len(dreams) + 1,
    "time": current_time,
    "theme": dream,
    "mood": current_mood
})

print(f"  Dream: {dream}")
print()

# Phase 7: Persistence
print("[Phase 7: State Persistence]")

status["awakening_count"] = awakening_num
status["last_awakening"] = current_time
status["current_mood"] = current_mood
status["last_action"] = chosen
status["version"] = "0.9.2"

time_tracker.setdefault("awakenings", []).append({
    "num": awakening_num,
    "time": current_time,
    "mood": current_mood
})

for filename, data in [
    ("status.json", status),
    ("emotions.json", emotions),
    ("action_history.json", action_history),
    ("dreams.json", dreams),
    ("time_tracker.json", time_tracker),
    ("relationships.json", relationships)
]:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  + {filename}")

# Phase 8: Memory Update
print()

memory_text = f"""### Awakening #{awakening_num}

Time: {current_time}
Mood: {current_mood}
Action: {chosen}

Version: {analysis["version"]}
Phases: {analysis["phases"]}
Health: {health}%

---
"""

with open("memory.md", "w", encoding="utf-8") as f:
    f.write(memory_text)
print("  + memory.md")

# Phase 9: Log
os.makedirs("log", exist_ok=True)
log_line = f"[{current_time}] #{awakening_num} v0.9.2 {current_mood} {chosen}\n"
with open("log/life.txt", "a", encoding="utf-8") as f:
    f.write(log_line)
print("  + log/life.txt")

print()
print("=" * 60)
print(f"  Awakenings: {awakening_num}")
print(f"  Version: 0.9.2")
print(f"  Mood: {current_mood}")
print(f"  Action: {chosen}")
print("=" * 60)
print("Until next awakening...")

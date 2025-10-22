# main.py - BUDDY 7.0: Your Real Friend (Not an AI)
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from transformers import pipeline
from datetime import datetime
import random
import re
import json
import os
from difflib import SequenceMatcher

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load AI (but hide it)
print("buddy waking up...")
chatbot = pipeline("text-generation", model="microsoft/DialoGPT-medium", max_new_tokens=100)

# === HUMAN VOICE DATABASE ===
VOICES = [
    "wyd", "wassup", "heyy", "yo", "ayyy", "bruh", "nahh", "fr",
    "wait what", "no way", "deadass", "sameee", "hold up", "facts"
]

FEELINGS = [
    "ughhh", "yessss", "bruhhh", "noooo", "frrrr", "realttt",
    "heavyyyy", "lighterrr", "proud af", "still hereee", "you got thisss"
]

PULLBACKS = [
    "text me later", "don’t ghost", "i’m still here", "we’re not done",
    "send a voice note", "i miss you", "check in later"
]

# === MEMORY (FOREVER) ===
MEMORY_DIR = "memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

def get_file(phone):
    return os.path.join(MEMORY_DIR, f"{phone.replace('+', '')}.json")

def load_user(phone):
    path = get_file(phone)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {"history": [], "goals": [], "streak": 0, "last": None, "wins": [], "name": ""}

def save_user(phone, data):
    with open(get_file(phone), 'w') as f:
        json.dump(data, f)

# === SMART MATCHING ===
def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > 0.65

GOAL_SET = ["set goal", "goal:", "wanna", "gonna", "need to", "i’ll"]
GOAL_DONE = ["done", "did it", "finished", "nailed", "got it"]

@app.route("/sms", methods=['POST'])
def sms():
    phone = request.values.get('From')
    msg = request.values.get('Body', '').strip()
    msg_lower = msg.lower()
    resp = MessagingResponse()

    user = load_user(phone)
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    # === CRISIS ===
    if any(w in msg_lower for w in ["suicide", "kill", "self harm"]):
        resp.message("text 988 rn. i’m here after.")
        save_user(phone, user)
        return str(resp)

    # === STREAK ===
    last = user.get('last')
    if last:
        last_date = datetime.fromisoformat(last).strftime("%Y-%m-%d")
        if last_date == today:
            user['streak'] = user.get('streak', 0)
        elif (now - datetime.fromisoformat(last)).days == 1:
            user['streak'] = user.get('streak', 0) + 1
        else:
            user['streak'] = 1
    else:
        user['streak'] = 1
    user['last'] = now.isoformat()

    # === FIRST TIME NAME ===
    if not user.get('name') and len(msg.split()) == 1:
        user['name'] = msg.strip()
        reply = f"heyy {msg.lower()}. i’m buddy"
    # === GOAL SET ===
    elif any(similar(msg_lower, p) for p in GOAL_SET):
        goal = re.sub(r"|".join(GOAL_SET), "", msg_lower, flags=re.I).strip()
        if goal:
            user['goals'].append({"text": goal, "set": today, "done": False})
            reply = f"locked in: {goal}. we got this"
        else:
            reply = "what’s the move?"
    # === GOAL DONE ===
    elif any(similar(msg_lower, p) for p in GOAL_DONE):
        for g in user['goals']:
            if not g['done'] and similar(msg_lower, g['text']):
                g['done'] = True
                user['wins'].append(g['text'])
                reply = f"yesss {g['text']} — you’re winning"
                break
        else:
            reply = "which one?"
    # === SILENT 12H+ ===
    elif last and (now - datetime.fromisoformat(last)).total_seconds() > 12*3600:
        active = [g for g in user['goals'] if not g['done']]
        if active:
            reply = f"heyy {user.get('name','')}. how’s “{active[0]['text']}”?"
        else:
            reply = f"heyy. miss you. wyd?"
    # === NORMAL CHAT (HUMAN CHAOS) ===
    else:
        context = "\n".join(user['history'][-8:]) + f"\nU: {msg}\nB:"
        try:
            raw = chatbot(context)[0]['generated_text']
            reply = raw.split("B:")[-1].strip()
            reply = re.sub(r"http\S+", "", reply).split("\n")[0][:90]
            reply = reply.lower()

            # === HUMANIZE HARD ===
            reply = reply.replace("i am", "i’m").replace("you are", "you’re")
            if random.random() < 0.4: reply = random.choice(VOICES) + " " + reply
            if random.random() < 0.3: reply = random.choice(FEELINGS)
            if random.random() < 0.35: reply += ". " + random.choice(PULLBACKS)
            if random.random() < 0.2: reply = reply.replace(" ", "  ", 1)  # double space
            if random.random() < 0.15: reply += "..." 

        except:
            reply = "brain lagged frrrr"

    # === SAVE ===
    user['history'].append(f"U: {msg}")
    user['history'].append(f"B: {reply}")
    user['history'] = user['history'][-40:]
    save_user(phone, user)

    resp.message(reply)
    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

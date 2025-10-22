# main.py - BUDDY: Your Real SMS Bestie
from flask import Flask, request, session
from twilio.twiml.messaging_response import MessagingResponse
from transformers import pipeline
import random
import re

app = Flask(__name__)
app.secret_key = "buddy_secret_2025"

# Load AI
print("Loading Buddy's brain...")
chatbot = pipeline("text-generation", model="microsoft/DialoGPT-medium", max_new_tokens=80)

# Natural slang & pullbacks
SLANG = ["fr", "no cap", "bet", "deadass", "lowkey", "highkey", "same", "real"]
PULLBACKS = ["text me later", "don’t leave me on read", "i’m here when you need", "we’re not done talking"]
CRISIS = ["suicide", "kill myself", "self harm", "end it", "don't want to live"]

# Subtle emoji (25% chance, 1 max)
EMOJIS = ["", "", "", "", "😭", "💀", "🔥", "🤍", "🫶", "💪"]

@app.route("/sms", methods=['POST'])
def sms():
    msg = request.values.get('Body', '').strip().lower()
    resp = MessagingResponse()

    # CRISIS FIRST
    if any(word in msg for word in CRISIS):
        resp.message("Please text 988 right now. I'm here after.")
        return str(resp)

    # MEMORY
    history = session.get('history', [])
    context = "\n".join(history[-3:]) + f"\nUser: {msg}\nBuddy:"

    try:
        raw = chatbot(context)[0]['generated_text']
        reply = raw.split("Buddy:")[-1].strip()
        reply = re.sub(r"http\S+", "", reply)
        reply = reply.split("\n")[0]

        # Humanize
        reply = reply.replace("I am", "I'm").replace("do not", "don't")
        reply = reply.replace("you are", "you're").replace("cannot", "can't")

        # Shorten
        if len(reply) > 80:
            reply = reply[:77] + "..."

        # 30% slang
        if random.random() < 0.3:
            reply = random.choice(SLANG) + " " + reply

        # 20% pullback
        if random.random() < 0.2:
            reply += ", " + random.choice(PULLBACKS)

        # 25% emoji
        if random.random() < 0.25:
            reply += " " + random.choice([e for e in EMOJIS if e])

    except:
        reply = "my brain lagged, try again"

    # SAVE MEMORY
    history.append(f"User: {msg}")
    history.append(f"Buddy: {reply}")
    session['history'] = history[-6:]

    resp.message(reply)
    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

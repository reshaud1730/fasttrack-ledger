from flask import Flask
from threading import Thread
import logging

app = Flask('')

# Suppress Flask's default logging to keep your console clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def home():
    return "Raytown Construction Ledger Bot is Online! 🏎️"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

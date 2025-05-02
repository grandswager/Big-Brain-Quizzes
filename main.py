from flask import Flask
from flask import session, request
import uuid

import os
from dotenv import dotenv_values

config = dotenv_values(".env")

app = Flask(__name__)
try:
    app.config["SECRET_KEY"] = config["APP_SECRET_KEY"] or os.environ.get("APP_SECRET_KEY")
except KeyError:
    print(".env file not found, using os.environ")

from events import *
from routes import *

if __name__ == '__main__':
    socketio.run(app, debug=False, allow_unsafe_werkzeug=True, host='0.0.0.0', port=4010)

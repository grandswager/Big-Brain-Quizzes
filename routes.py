from flask import render_template, request, redirect, session
from main import app

import os
from dotenv import dotenv_values

config = dotenv_values(".env")
try:
    ADMIN_PIN = config["ADMIN_PIN"]
except KeyError:
    ADMIN_PIN = os.environ.get("ADMIN_PIN")
    print(".env file not found, using os.environ")

@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    global ADMIN_PIN
    if request.method == 'POST':
        pin = request.form.get('pin')
        if pin == ADMIN_PIN:
            session['admin_authenticated'] = True
            return redirect('/admin')
        else:
            return 'Invalid PIN', 401
    return render_template('login.html')

@app.route('/admin')
def admin_panel():
    if not session.get('admin_authenticated'):
        return redirect('/login')
    return render_template('admin.html')


# master_of_jokes/admin.py
import functools
import re
import logging
logger = logging.getLogger(__name__)
import hashlib


from flask import (
    Blueprint, flash, g, redirect, session, render_template, request, url_for
)
from master_of_jokes.db import get_db

import logging
bp = Blueprint('auth', __name__, url_prefix='/auth')
logger = logging.getLogger(__name__)
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

@bp.before_app_request
def load_logged_in_user():

    user_id = session.get('user_id')
    logger.debug("Loading user from session: %s", user_id)

    if user_id is None:
        logger.debug("No user session found")
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        logger.debug("Received POST to /register") # DEBUG

        email = request.form['email']
        nickname = request.form['nickname']
        password = request.form['password']
        db = get_db()
        error = None

        if not email:
            error = 'Email is required.'
            logger.warning("Registration failed: %s", error)
        elif not nickname:
            error = 'Nickname is required.'
            logger.warning("Registration failed: %s", error)
        elif not password:
            error = 'Password is required.'
            logger.warning("Registration failed: %s", error)
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            error = 'Invalid email format.'
            logger.warning("Registration failed: %s", error)
        elif db.execute(
            'SELECT id FROM user WHERE email = ?', (email,)
        ).fetchone() is not None:
            error = f"Email {email} is already registered."
        elif db.execute(
            'SELECT id FROM user WHERE nickname = ?', (nickname,)
        ).fetchone() is not None:
            error = f"Nickname {nickname} is already taken."

        if error is None:
            logger.info("New user registered: %s", nickname)
            # Create a custom password hash instead of using Werkzeug's default
            # which might use scrypt on some systems
            password_hash = 'pbkdf2:sha256:' + hashlib.pbkdf2_hmac(
                'sha256', 
                password.encode('utf-8'), 
                hashlib.sha256(email.encode('utf-8')).digest(), 
                100000
            ).hex()
            
            db.execute(
                'INSERT INTO user (email, nickname, password, role) VALUES (?, ?, ?, ?)',
                (email, nickname, password_hash, 'user')  # <- add 'user' here
                )
            db.commit()
            logger.info("Registered new user %s", nickname)
            return redirect(url_for('auth.login'))
        logger.warning("Registration failed: %s", error)
        flash(error)

    logger.debug("Exiting register()")
    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        logger.debug("Login POST request received")

        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        user = db.execute(
            'SELECT * FROM user WHERE email = ? OR nickname = ?',
            (username, username)
        ).fetchone()

        if user is None:
            error = 'Incorrect username or password.'
            logger.warning("Login failed: No user found for %s", username)
        else:
            stored_pw = user['password']
            if stored_pw.startswith('pbkdf2:sha256:') and len(stored_pw.split('$')) == 3:
                # Werkzeug hash
                from werkzeug.security import check_password_hash
                if not check_password_hash(stored_pw, password):
                    error = 'Incorrect username or password.'
            else:
                # Custom hash (what your register() function creates)
                stored_hash = stored_pw.split(':', 2)[2]
                computed_hash = hashlib.pbkdf2_hmac(
                    'sha256',
                    password.encode('utf-8'),
                    hashlib.sha256(user['email'].encode('utf-8')).digest(),
                    100000
                ).hex()
                if stored_hash != computed_hash:
                    error = 'Incorrect username or password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            logger.info("User logged in: %s", user['nickname'])
            return redirect(url_for('jokes.create'))

        flash(error)

    logger.debug("Exiting login()")
    return render_template('auth/login.html')



@bp.route('/logout')
def logout():
    logger.info("User logged out: %s", g.user['nickname'] if g.user else 'Unknown')
    session.clear()
    return redirect(url_for('index'))

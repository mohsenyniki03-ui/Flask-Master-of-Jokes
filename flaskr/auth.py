import functools
import re

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


def is_valid_email(email):
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_nickname(nickname):
    """Validate nickname: 3-20 characters, alphanumeric and underscores only."""
    if len(nickname) < 3 or len(nickname) > 20:
        return False
    pattern = r'^[a-zA-Z0-9_]+$'
    return re.match(pattern, nickname) is not None


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = (
            get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        )


@bp.route("/register", methods=("GET", "POST"))
def register():
    """Register a new user.

    Validates that the username is not already taken. Hashes the
    password for security.
    """
    if request.method == "POST":
        username = request.form["username"].strip()
        nickname = request.form["nickname"].strip()
        password = request.form["password"]
        confirm_password = request.form.get("confirm-password", "")
        db = get_db()
        error = None

        # Validation
        if not username:
            error = "Email address is required."
        elif not is_valid_email(username):
            error = "Please enter a valid email address."
        elif not nickname:
            error = "Nickname is required."
        elif not is_valid_nickname(nickname):
            error = "Nickname must be 3-20 characters and contain only letters, numbers, and underscores."
        elif not password:
            error = "Password is required."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif db.execute(
            "SELECT id FROM user WHERE username = ?", (username,)
        ).fetchone() is not None:
            error = f"Email {username} is already registered."
        elif db.execute(
            "SELECT id FROM user WHERE nickname = ?", (nickname,)
        ).fetchone() is not None:
            error = f"Nickname '{nickname}' is already taken. Please choose another."

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, nickname, password) VALUES (?, ?, ?)",
                    (username, nickname, generate_password_hash(password, method='pbkdf2:sha256')),
                )
                db.commit()
            except db.IntegrityError:
                error = "An error occurred during registration. Please try again."
            else:
                # Success, go to the login page.
                flash("Account created successfully! Please log in.")
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Log in a registered user by adding the user id to the session."""
    if request.method == "POST":
        identifier = request.form["username"].strip() # for email (username) OR nickname
        password = request.form["password"]
        db = get_db()
        error = None

        if not identifier:
            error = "Email or nickname is required."
        elif not password:
            error = "Password is required."
        else:
            user = db.execute(
                "SELECT * FROM user WHERE username = ? OR nickname = ?", (identifier, identifier)
            ).fetchone()

            if user is None:
                error = "Invalid email/nickname or password."
            elif not check_password_hash(user["password"], password):
                error = "Invalid email/nickname or password."

        if error is None:
            # store the user id in a new session and return to the index
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("jokes.leave"))

        flash(error)

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for("index"))



@bp.route("/profile/<username>")
def profile(username):
    """Display user profile with stats and jokes."""
    db = get_db()
    
    # Fetch user by username (email) or nickname
    user = db.execute(
        "SELECT * FROM user WHERE username = ? OR nickname = ?", 
        (username, username)
    ).fetchone()
    
    if user is None:
        flash(f"User '{username}' not found.")
        return redirect(url_for("index"))
    
    # Get user's jokes with ratings
    user_jokes = db.execute(
        """SELECT p.*, u.nickname as username, 
           COUNT(DISTINCT r.id) as rating_count,
           COALESCE(AVG(r.rating), 0) as avg_rating
           FROM post p
           JOIN user u ON p.author_id = u.id
           LEFT JOIN rating r ON p.id = r.post_id
           WHERE p.author_id = ?
           GROUP BY p.id
           ORDER BY p.created DESC""",
        (user["id"],)
    ).fetchall()
    
    # Calculate engagement metrics
    total_jokes = len(user_jokes)
    total_ratings = db.execute(
        """SELECT COUNT(*) as count FROM rating r
           JOIN post p ON r.post_id = p.id
           WHERE p.author_id = ?""",
        (user["id"],)
    ).fetchone()["count"]
    
    total_comments = db.execute(
        """SELECT COUNT(*) as count FROM comment c
           JOIN post p ON c.post_id = p.id
           WHERE p.author_id = ?""",
        (user["id"],)
    ).fetchone()["count"]
    
    # Calculate average rating across all jokes
    avg_rating_result = db.execute(
        """SELECT COALESCE(AVG(r.rating), 0) as avg_rating
           FROM rating r
           JOIN post p ON r.post_id = p.id
           WHERE p.author_id = ?""",
        (user["id"],)
    ).fetchone()
    overall_avg_rating = round(avg_rating_result["avg_rating"], 2)
    
    # Engagement score: weighted combination of jokes, ratings, comments
    engagement_score = (total_jokes * 10) + (total_ratings * 2) + (total_comments * 3)
    
    return render_template(
        "auth/profile.html",
        profile_user=user,
        user_jokes=user_jokes,
        total_jokes=total_jokes,
        total_ratings=total_ratings,
        total_comments=total_comments,
        overall_avg_rating=overall_avg_rating,
        engagement_score=engagement_score
    )

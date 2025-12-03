from flask import Blueprint
from flask import flash
from flask import g
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from .auth import login_required
from .db import get_db

bp = Blueprint("jokes", __name__)


@bp.route("/")
def index():
    """Show all the jokes, sorted by average rating (highest first)."""
    db = get_db()
    posts = db.execute(
        """SELECT p.id, p.title, p.body, p.created, p.author_id, u.username,
                  COALESCE(AVG(r.rating), 0) as avg_rating,
                  COUNT(DISTINCT r.id) as rating_count
           FROM post p 
           JOIN user u ON p.author_id = u.id
           LEFT JOIN rating r ON p.id = r.post_id
           GROUP BY p.id
           ORDER BY avg_rating DESC, p.created DESC"""
    ).fetchall()
    
    # Get user's ratings if logged in
    user_ratings = {}
    if g.user:
        ratings = db.execute(
            "SELECT post_id, rating FROM rating WHERE user_id = ?",
            (g.user['id'],)
        ).fetchall()
        user_ratings = {r['post_id']: r['rating'] for r in ratings}
    
    return render_template("jokes/index.html", jokes=posts, user_ratings=user_ratings)


def get_joke(id, check_author=True):
    """Get a joke and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    joke = (
        get_db()
        .execute(
            "SELECT p.id, title, body, created, author_id, username"
            " FROM post p JOIN user u ON p.author_id = u.id"
            " WHERE p.id = ?",
            (id,),
        )
        .fetchone()
    )

    if joke is None:
        abort(404, f"Joke id {id} doesn't exist.")

    if check_author and joke["author_id"] != g.user["id"]:
        abort(403)

    return joke


@bp.route("/leave", methods=("GET", "POST"))
@login_required
def leave():
    """Leave a new joke as the current user."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if len(title.split()) > 10 :
            error = 'Title can only be 10 words'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                (title, body, g.user["id"]),
            )
            db.commit()
            return redirect(url_for("jokes.index"))

    return render_template("jokes/leave.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a joke if the current user is the author."""
    joke = get_joke(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE post SET title = ?, body = ? WHERE id = ?", (title, body, id)
            )
            db.commit()
            return redirect(url_for("jokes.index"))

    return render_template("jokes/update.html", joke=joke)


@bp.route("/<int:id>/rate", methods=("POST",))
@login_required
def rate(id):
    """Rate a joke with 1-5 stars."""
    rating_value = request.form.get("rating", type=int)
    
    if not rating_value or rating_value < 1 or rating_value > 5:
        return jsonify({"error": "Invalid rating"}), 400
    
    db = get_db()
    
    # Check if joke exists
    joke = db.execute("SELECT id FROM post WHERE id = ?", (id,)).fetchone()
    if joke is None:
        return jsonify({"error": "Joke not found"}), 404
    
    try:
        # Insert or update rating
        db.execute(
            """INSERT INTO rating (post_id, user_id, rating) 
               VALUES (?, ?, ?)
               ON CONFLICT(post_id, user_id) 
               DO UPDATE SET rating = ?, created = CURRENT_TIMESTAMP""",
            (id, g.user['id'], rating_value, rating_value)
        )
        db.commit()
        
        # Get updated average rating
        result = db.execute(
            """SELECT COALESCE(AVG(rating), 0) as avg_rating,
                      COUNT(*) as rating_count
               FROM rating WHERE post_id = ?""",
            (id,)
        ).fetchone()
        
        return jsonify({
            "success": True,
            "avg_rating": round(result['avg_rating'], 1),
            "rating_count": result['rating_count']
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_joke(id)
    db = get_db()
    db.execute("DELETE FROM post WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("jokes.index"))

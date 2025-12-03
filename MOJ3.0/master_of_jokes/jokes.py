from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from master_of_jokes.auth import login_required # type: ignore
from master_of_jokes.db import get_db # type: ignore

import logging
logger = logging.getLogger(__name__)

bp = Blueprint('jokes', __name__)


@bp.route('/')
def index():
    """Redirect to create joke page if logged in, otherwise to login page."""
    if g.user:
        return redirect(url_for('jokes.create'))
    return redirect(url_for('auth.login'))


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    """Create a new joke."""
    if request.method == 'POST':
        logger.debug("Entered create() view for user %s", g.user['nickname'])

        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'
        elif not body:
            error = 'Body is required.'
        elif len(title.split()) > 10:
            error = 'Title cannot be more than 10 words.'
        
        if error is None:
            db = get_db()
            try:
                logger.info("Joke created: '%s' by %s", title, g.user['nickname'])

                # Insert the joke
                db.execute(
                    'INSERT INTO joke (author_id, title, body)'
                    ' VALUES (?, ?, ?)',
                    (g.user['id'], title, body)
                )
                
                # Update user's joke balance
                db.execute(
                    'UPDATE user SET joke_balance = joke_balance + 1'
                    ' WHERE id = ?',
                    (g.user['id'],)
                )
                
                db.commit()
                return redirect(url_for('jokes.my_jokes'))
            except db.IntegrityError:
                logger.warning("Joke creation failed for user %s: %s", g.user['nickname'], error)

                error = f"You already have a joke with title '{title}'."
        
        flash(error)

    return render_template('jokes/create.html')


@bp.route('/my-jokes')
@login_required
def my_jokes():
    """Show jokes created by the logged-in user."""
    logger.info("User %s requested their joke list", g.user['nickname'])

    db = get_db()
    jokes = db.execute(
        'SELECT j.id, title, body, created, author_id, nickname,'
        ' COALESCE(AVG(r.rating), 0) as avg_rating'
        ' FROM joke j JOIN user u ON j.author_id = u.id'
        ' LEFT JOIN joke_rating r ON j.id = r.joke_id'
        ' WHERE j.author_id = ?'
        ' GROUP BY j.id'
        ' ORDER BY created DESC',
        (g.user['id'],)
    ).fetchall()
    logger.debug("Fetched %d jokes for user %s", len(jokes), g.user['nickname'])

    return render_template('jokes/my_jokes.html', jokes=jokes)


@bp.route('/list')
@login_required
def list_jokes():
    logger.info("User %s requested list of public jokes", g.user['nickname'])

    """List all jokes not authored by the current user."""
    db = get_db()
    jokes = db.execute(
        'SELECT j.id, title, author_id, nickname,'
        ' COALESCE(AVG(r.rating), 0) as avg_rating'
        ' FROM joke j JOIN user u ON j.author_id = u.id'
        ' LEFT JOIN joke_rating r ON j.id = r.joke_id'
        ' WHERE j.author_id != ?'
        ' GROUP BY j.id'
        ' ORDER BY created DESC',
        (g.user['id'],)
    ).fetchall()
    logger.debug("Fetched %d non-authored jokes for user %s", len(jokes), g.user['nickname'])

    return render_template('jokes/list.html', jokes=jokes)


def get_joke(id, check_author=True):
    """Get a joke by id and optionally check if current user is the author."""
    joke = get_db().execute(
        'SELECT j.id, title, body, created, author_id, nickname,'
        ' COALESCE(AVG(r.rating), 0) as avg_rating,'
        ' COUNT(r.id) as rating_count'
        ' FROM joke j JOIN user u ON j.author_id = u.id'
        ' LEFT JOIN joke_rating r ON j.id = r.joke_id'
        ' WHERE j.id = ?'
        ' GROUP BY j.id',
        (id,)
    ).fetchone()

    if joke is None:
        abort(404, f"Joke id {id} doesn't exist.")

    if check_author and joke['author_id'] != g.user['id']:
        abort(403)

    return joke


@bp.route('/<int:id>/view', methods=('GET', 'POST'))
@login_required
def view(id):
    logger.info("User %s is viewing joke ID %s", g.user['nickname'], id)

    """View a specific joke and handle rating if the user is not the author."""
    db = get_db()
    joke = db.execute(
        'SELECT j.id, title, body, created, author_id, nickname,'
        ' COALESCE(AVG(r.rating), 0) as avg_rating'
        ' FROM joke j JOIN user u ON j.author_id = u.id'
        ' LEFT JOIN joke_rating r ON j.id = r.joke_id'
        ' WHERE j.id = ?'
        ' GROUP BY j.id',
        (id,)
    ).fetchone()
    
    if joke is None:
        logger.error("Joke not found: ID %s requested by %s", id, g.user['nickname'])
        abort(404, f"Joke id {id} doesn't exist.")
    
    # Check if user has already viewed this joke
    view_record = db.execute(
        'SELECT * FROM joke_view WHERE user_id = ? AND joke_id = ?',
        (g.user['id'], id)
    ).fetchone()
    
    # Get user's current rating if any
    user_rating = db.execute(
        'SELECT rating FROM joke_rating WHERE user_id = ? AND joke_id = ?',
        (g.user['id'], id)
    ).fetchone()
    
    is_author = joke['author_id'] == g.user['id']
    
    # Handle rating submission
    if request.method == 'POST' and not is_author:
        rating = request.form.get('rating')
        if rating:
            try:
                rating = int(rating)
                if 1 <= rating <= 5:
                    logger.info("User %s rated joke ID %s with %s", g.user['nickname'], id, rating)

                    if user_rating:
                        db.execute(
                            'UPDATE joke_rating SET rating = ?'
                            ' WHERE user_id = ? AND joke_id = ?',
                            (rating, g.user['id'], id)
                        )
                    else:
                        db.execute(
                            'INSERT INTO joke_rating (user_id, joke_id, rating)'
                            ' VALUES (?, ?, ?)',
                            (g.user['id'], id, rating)
                        )
                    db.commit()
                    return redirect(url_for('jokes.view', id=id))
                else:
                    logger.warning("User %s submitted invalid rating: %s", g.user['nickname'], rating)

                    flash('Rating must be between 1 and 5.')
            except ValueError:
                flash('Invalid rating value.')
    
    # First time viewing the joke
    if not view_record and not is_author:
        user = db.execute(
            'SELECT joke_balance FROM user WHERE id = ?', 
            (g.user['id'],)
        ).fetchone()
        
        # Check joke balance
        if user['joke_balance'] <= 0:
            logger.warning("User %s tried to view a joke with 0 balance", g.user['nickname'])

            flash('You need to leave a joke first before viewing more jokes.')
            return redirect(url_for('jokes.my_jokes'))
        
        # Decrement joke balance and record the view
        logger.debug("Decremented joke balance for user %s", g.user['nickname'])

        db.execute(
            'UPDATE user SET joke_balance = joke_balance - 1 WHERE id = ?',
            (g.user['id'],)
        )
        db.execute(
            'INSERT INTO joke_view (user_id, joke_id) VALUES (?, ?)',
            (g.user['id'], id)
        )
        db.commit()
    
    return render_template('jokes/view.html', joke=joke, user_rating=user_rating)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    logger.info("User %s is updating joke ID %s", g.user['nickname'], id)

    """Update a joke."""
    joke = get_joke(id)

    if request.method == 'POST':
        body = request.form['body']
        error = None

        if not body:
            logger.warning("Update failed for joke ID %s: body was empty", id)
            error = 'Body is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE joke SET body = ? WHERE id = ?',
                (body, id)
            )
            logger.info("Joke ID %s updated by %s", id, g.user['nickname'])

            db.commit()
            return redirect(url_for('jokes.my_jokes'))

    return render_template('jokes/update.html', joke=joke)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    logger.info("User %s is deleting joke ID %s", g.user['nickname'], id)

    """Delete a joke."""
    joke = get_joke(id)
    db = get_db()
    
    # First delete related records in joke_view and joke_rating
    db.execute('DELETE FROM joke_view WHERE joke_id = ?', (id,))
    db.execute('DELETE FROM joke_rating WHERE joke_id = ?', (id,))
    
    # Then delete the joke
    db.execute('DELETE FROM joke WHERE id = ?', (id,))
    logger.debug("Deleted joke ID %s and related views/ratings", id)

    db.commit()
    
    return redirect(url_for('jokes.my_jokes'))
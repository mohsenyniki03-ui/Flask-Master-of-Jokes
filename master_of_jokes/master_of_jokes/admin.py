# master_of_jokes/admin.py
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from master_of_jokes.db import get_db
from master_of_jokes.auth import login_required
import logging
bp = Blueprint('moderator', __name__, url_prefix='/admin')
logger = logging.getLogger(__name__)

def moderator_required(view):
    from functools import wraps
    
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user['role'] != 'moderator':
            flash("moderator access only.")
            return redirect(url_for('index'))

        logger.debug("Moderator is startting for %s",g.user['nickname'])    
        return view(**kwargs)
    
    return wrapped_view


@bp.route('/')
@login_required
@moderator_required
def dashboard():
    logger.info("Moderator Dashboard started")
    db = get_db()
    users = db.execute("SELECT id, nickname, role, joke_balance FROM user").fetchall()
    logger.debug("Showing %s dashboard",g.user['nickname'])
    return render_template('admin/dashboard.html', users=users)

@bp.route('/promote', methods=['POST'])
@login_required
@moderator_required
def promote():
    logger.info("The user is being promoted")
    user_id = request.form['user_id']
    db = get_db()
    db.execute("UPDATE user SET role = 'moderator' WHERE id = ?", (user_id,))
    db.commit()
    flash("User promoted to Moderator.")
    logger.debug("User %s being promoted",g.user['nickname'])
    return redirect(url_for('moderator.dashboard'))


@bp.route('/demote', methods=['POST'])
@login_required
@moderator_required
def demote():
    logger.info("Taking moderator status off")
    user_id = request.form['user_id']
    db = get_db()
    # Ensure we are not removing the last moderator
    count = db.execute("SELECT COUNT(*) FROM user WHERE role = 'moderator'").fetchone()[0]
    if count > 1:
        db.execute("UPDATE user SET role = 'user' WHERE id = ?", (user_id,))
        db.commit()
        flash("Moderator demoted to User.")
    else:
        logger.warning("Can't take last moderator")
        flash("You can't remove the last moderator.")
    logger.debug("User %s moderator being taken",g.user['nickname'])
    return redirect(url_for('moderator.dashboard'))

@bp.route('/update-balance', methods=['POST'])
@login_required
@moderator_required
def update_balance():
    logger.debug("The database is initializing")
    logger.info("Database starting")
    db = get_db()
    db.execute("UPDATE user SET joke_balance = ? WHERE id = ?", (request.form['new_balance'], request.form['user_id']))
    db.commit()
    logger.debug("Database was initialized")
    flash("Balance updated.")
    return redirect(url_for('moderator.dashboard'))


import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext

import logging
logger = logging.getLogger(__name__)


def get_db():
    if 'db' not in g:
        logger.debug("Opening new DB connection to: %s", current_app.config['DATABASE'])
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    logger.debug("DB connection established with row factory")

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()
        logger.debug("Closing DB connection")


def init_db():
    logger.info("Initializing the database")
    db = get_db()
    logger.info("Database initialized: %s", db)
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
    logger.info("Ran CLI: init-db")
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    import click

@click.command('init-moderator')
@click.argument('email')
@click.argument('nickname')
@click.argument('password')
@with_appcontext
def init_moderator_command(email, nickname, password):
    db = get_db()
    from hashlib import pbkdf2_hmac, sha256
    password_hash = 'pbkdf2:sha256:' + pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        sha256(email.encode('utf-8')).digest(),
        100000
    ).hex()
    db.execute(
        'INSERT INTO user (email, nickname, password, role) VALUES (?, ?, ?, ?)',
        (email, nickname, password_hash, 'Moderator')
    )
    db.commit()
    click.echo(f'Moderator {nickname} created.')

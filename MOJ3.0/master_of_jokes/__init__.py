import os
import click

import logging
from logging.config import dictConfig
from flask import Flask, request  

from flask import Flask
from .db import get_db

from flask_cors import CORS


def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    from flask_cors import CORS
    CORS(app)

    dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] [%(levelname)s] %(module)s: %(message)s',
                'datefmt': '%Y-%m-%dT%H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': 'DEBUG', 
            },
            'file': {
                'class': 'logging.FileHandler', 
                'filename': 'moj.log',
                'formatter': 'default', 
                'level': 'INFO',
            },
        },
        'root': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
        },
    })
    logger = logging.getLogger(__name__)
    logger.info("🟢 Starting Master of Jokes app")

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'master_of_jokes.sqlite'),
    )
    logger.info("Database configured at: %s", app.config['DATABASE'])

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
        logger.info("Loaded config from config.py")
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)
        logger.info("Loaded test config")

    if not app.config.get('SECRET_KEY'):
        logger.critical("CRITICAL: SECRET_KEY is not set! The application is running insecurely.")

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError as e:
        logger.error("Failed to create instance folder: %s", e)
        pass

    # Register database functions
    from . import db
    db.init_app(app)
    logger.info("Database functions registered")

    # Register blueprints
    from . import auth
    app.register_blueprint(auth.bp)

    from . import jokes
    app.register_blueprint(jokes.bp)
    app.add_url_rule('/', endpoint='index')

    from . import admin
    app.register_blueprint(admin.bp)


    @app.cli.command("init-moderator")
    @click.argument("email")
    @click.argument("nickname")
    @click.argument("password")

    def init_moderator(email, nickname, password):
        """Create a moderator account via CLI."""
        from . import db
        from werkzeug.security import generate_password_hash

        db = get_db()
        try:
            db.execute(
                "INSERT INTO user (email, nickname, password, role) VALUES (?, ?, ?, ?)",
                (email, nickname, generate_password_hash(password), "moderator")
            )

            db.commit()
            logger.info("Moderator initialized: %s", nickname)
            click.echo(f"Moderator {nickname} created.")
        except db.IntegrityError:
            logger.warning("Attempt to re-create existing moderator: %s", nickname)
            click.echo("User already exists.")

    @app.before_request
    def log_session():
        from flask import session
        logger = logging.getLogger(__name__)
        logger.debug("Session ID: %s", session.get('user_id', 'anonymous'))

    @app.after_request
    def log_response(response):
        logger.info("Returned %s for %s %s", response.status_code, request.method, request.path)
        return response

    from . import report_api
    app.register_blueprint(report_api.bp)

    return app

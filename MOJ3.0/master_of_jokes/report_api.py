from flask import Blueprint, jsonify
from master_of_jokes.db import get_db

bp = Blueprint('report_api', __name__, url_prefix='/api/status')

@bp.route('/users')
def user_count():
    db = get_db()
    count = db.execute('SELECT COUNT(*) FROM user').fetchone()[0]
    return jsonify({'count': count})

@bp.route('/jokes')
def joke_count():
    db = get_db()
    count = db.execute('SELECT COUNT(*) FROM joke').fetchone()[0]
    return jsonify({'count': count})

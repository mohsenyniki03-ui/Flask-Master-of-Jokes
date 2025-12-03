#!/usr/bin/env python3
"""
Migration script to add comment table to existing database.
Run this script to update your database without losing existing data.
"""

import sqlite3
import os

# Get the instance folder path
instance_path = os.path.join(os.path.dirname(__file__), 'instance')
db_path = os.path.join(instance_path, 'flaskr.sqlite')

if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
    print("Please make sure you've initialized the database first.")
    exit(1)

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if comment table already exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='comment'")
if cursor.fetchone():
    print("Comment table already exists. No migration needed.")
    conn.close()
    exit(0)

print("Adding comment table...")

try:
    # Create comment table
    cursor.execute('''
        CREATE TABLE comment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES post (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    print("✓ Successfully added comment table!")
    print("✓ Migration complete!")
    
except sqlite3.Error as e:
    print(f"✗ Error during migration: {e}")
    conn.rollback()
    exit(1)
finally:
    conn.close()

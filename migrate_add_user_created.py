"""
Migration script to add 'created' column to user table.
Run this script once to update existing database.
"""
import sqlite3
from datetime import datetime

def migrate():
    """Add created column to user table if it doesn't exist."""
    conn = sqlite3.connect('instance/flaskr.sqlite')
    cursor = conn.cursor()
    
    try:
        # Check if created column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'created' not in columns:
            print("Adding 'created' column to user table...")
            
            # Add the created column without default (SQLite limitation when altering table)
            cursor.execute("""
                ALTER TABLE user 
                ADD COLUMN created TIMESTAMP
            """)
            
            # Update existing users with current timestamp
            cursor.execute("""
                UPDATE user 
                SET created = CURRENT_TIMESTAMP 
                WHERE created IS NULL
            """)
            
            conn.commit()
            print("✅ Successfully added 'created' column to user table!")
        else:
            print("ℹ️  'created' column already exists in user table.")
            
    except sqlite3.Error as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()

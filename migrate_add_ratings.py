"""
Migration script to add ratings table to existing database.
This preserves existing users and jokes.
"""

import sqlite3

def migrate_database():
    """Add ratings table to existing database."""
    
    db = sqlite3.connect('instance/flaskr.sqlite')
    
    print("🔄 Starting database migration...")
    
    try:
        # Create ratings table
        db.execute("""
            CREATE TABLE IF NOT EXISTS rating (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES post (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
                UNIQUE (post_id, user_id)
            )
        """)
        
        db.commit()
        print("✅ Successfully added ratings table!")
        print("📊 Database migration complete!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_database()

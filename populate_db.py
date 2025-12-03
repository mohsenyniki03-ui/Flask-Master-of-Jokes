"""
Script to populate the database with sample users and jokes for testing.
Run this script from the project root directory.
"""

import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

# Sample data
SAMPLE_USERS = [
    ("alice@example.com", "alice_laughs", "password"),
    ("bob@example.com", "bob_jokes", "password"),
    ("charlie@example.com", "charlie_comedy", "password"),
    ("diana@example.com", "diana_giggles", "password"),
    ("eve@example.com", "eve_humor", "password"),
    ("frank@example.com", "frank_funny", "password"),
    ("grace@example.com", "grace_grins", "password"),
    ("henry@example.com", "henry_hilarious", "password"),
    ("iris@example.com", "iris_jester", "password"),
    ("jack@example.com", "jack_joker", "password"),
]

SAMPLE_JOKES = [
    # Classic one-liners
    ("Why did the scarecrow win an award?", "Because he was outstanding in his field!"),
    ("Why don't scientists trust atoms?", "Because they make up everything!"),
    ("What do you call fake spaghetti?", "An impasta!"),
    ("Why did the bicycle fall over?", "Because it was two-tired!"),
    ("What do you call cheese that isn't yours?", "Nacho cheese!"),
    
    # Programming jokes
    ("Why do programmers prefer dark mode?", "Because light attracts bugs!"),
    ("How many programmers does it take to change a light bulb?", "None, that's a hardware problem!"),
    ("Why do Java developers wear glasses?", "Because they don't C#!"),
    ("What's a programmer's favorite hangout place?", "Foo Bar!"),
    ("Why did the developer go broke?", "Because he used up all his cache!"),
    
    # Food jokes
    ("What did the grape say when it got stepped on?", "Nothing, it just let out a little wine!"),
    ("Why did the tomato turn red?", "Because it saw the salad dressing!"),
    ("What do you call a fake noodle?", "An impasta!"),
    ("Why did the cookie go to the doctor?", "Because it felt crumbly!"),
    ("What's orange and sounds like a parrot?", "A carrot!"),
    
    # Animal jokes
    ("What do you call a bear with no teeth?", "A gummy bear!"),
    ("Why don't elephants use computers?", "They're afraid of the mouse!"),
    ("What do you call a sleeping bull?", "A bulldozer!"),
    ("Why do fish live in salt water?", "Because pepper makes them sneeze!"),
    ("What do you call a pig that does karate?", "A pork chop!"),
    
    # Dad jokes
    ("I'm reading a book about anti-gravity", "It's impossible to put down!"),
    ("Did you hear about the restaurant on the moon?", "Great food, no atmosphere!"),
    ("Why can't you hear a pterodactyl use the bathroom?", "Because the P is silent!"),
    ("What time did the man go to the dentist?", "Tooth hurty!"),
    ("Why did the math book look so sad?", "Because it had too many problems!"),
    
    # Science jokes
    ("Why is it bad to trust an atom?", "They make up everything!"),
    ("What did one DNA strand say to the other?", "Do these genes make me look fat?"),
    ("Why did the photon check into a hotel?", "Because it was traveling light!"),
    ("How do you organize a space party?", "You planet!"),
    ("What's the best thing about Switzerland?", "I don't know, but the flag is a big plus!"),
    
    # Tech jokes
    ("Why was the computer cold?", "It left its Windows open!"),
    ("What do computers eat for a snack?", "Microchips!"),
    ("Why did the smartphone need glasses?", "It lost all its contacts!"),
    ("What do you call a computer superhero?", "A screen saver!"),
    ("Why did the PowerPoint presentation cross the road?", "To get to the other slide!"),
    
    # School jokes
    ("Why did the student eat his homework?", "Because the teacher said it was a piece of cake!"),
    ("What's the king of all school supplies?", "The ruler!"),
    ("Why was the geometry book so adorable?", "Because it had acute angles!"),
    ("What did the calculator say to the student?", "You can count on me!"),
    ("Why did the teacher wear sunglasses?", "Because her students were so bright!"),
    
    # Music jokes
    ("Why did the musician get locked out?", "Because he had the wrong key!"),
    ("What's a balloon's least favorite music?", "Pop music!"),
    ("Why did Beethoven get rid of his chickens?", "All they said was 'Bach, Bach, Bach!'"),
    ("What do you call a cow that plays music?", "A moo-sician!"),
    ("Why was the piano laughing?", "Someone was tickling the ivories!"),
    
    # More fun jokes
    ("Why don't eggs tell jokes?", "They'd crack each other up!"),
    ("What do you call a parade of rabbits hopping backwards?", "A receding hare-line!"),
    ("Why did the golfer bring two pairs of pants?", "In case he got a hole in one!"),
    ("What do you call a dinosaur that crashes cars?", "Tyrannosaurus Wrecks!"),
    ("Why don't skeletons fight each other?", "They don't have the guts!"),
]

def populate_database():
    """Populate the database with sample users and jokes."""
    
    # Connect to the database
    db = sqlite3.connect('instance/flaskr.sqlite')
    db.row_factory = sqlite3.Row
    
    print("🎭 Starting to populate the database...")
    print(f"📝 Creating {len(SAMPLE_USERS)} users...")
    
    # Insert users
    user_ids = []
    for email, nickname, password in SAMPLE_USERS:
        try:
            cursor = db.execute(
                "INSERT INTO user (username, nickname, password) VALUES (?, ?, ?)",
                (email, nickname, generate_password_hash(password, method='pbkdf2:sha256'))
            )
            user_ids.append(cursor.lastrowid)
            print(f"✅ Created user: {nickname} ({email})")
        except sqlite3.IntegrityError:
            print(f"⚠️  User {nickname} already exists, skipping...")
            # Get existing user ID
            result = db.execute("SELECT id FROM user WHERE nickname = ?", (nickname,)).fetchone()
            if result:
                user_ids.append(result['id'])
    
    db.commit()
    print(f"\n🎉 Successfully created {len(user_ids)} users!")
    
    # Insert jokes
    print(f"\n📝 Creating {len(SAMPLE_JOKES)} jokes...")
    
    jokes_created = 0
    base_date = datetime.now()
    
    for i, (title, body) in enumerate(SAMPLE_JOKES):
        # Randomly assign jokes to users
        author_id = random.choice(user_ids)
        
        # Create jokes with different timestamps (spread over the last 30 days)
        created_date = base_date - timedelta(days=random.randint(0, 30), 
                                            hours=random.randint(0, 23),
                                            minutes=random.randint(0, 59))
        
        try:
            db.execute(
                "INSERT INTO post (title, body, created, author_id) VALUES (?, ?, ?, ?)",
                (title, body, created_date, author_id)
            )
            jokes_created += 1
            print(f"✅ Created joke: '{title[:50]}...'")
        except Exception as e:
            print(f"⚠️  Error creating joke: {e}")
    
    db.commit()
    db.close()
    
    print(f"\n🎉 Successfully created {jokes_created} jokes!")
    print(f"\n✨ Database population complete!")
    print(f"📊 Total: {len(user_ids)} users and {jokes_created} jokes")
    print(f"\n🔑 All users have password: 'password'")
    print(f"🌐 Start your Flask app and visit http://127.0.0.1:5000 to see the jokes!")

if __name__ == "__main__":
    populate_database()

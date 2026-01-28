from faker import Faker
from app import app, db, User 
from werkzeug.security import generate_password_hash
import random

fake = Faker()

def create_test_players(num_players=100):
    """Creates fake players with random stats for leaderboard testing"""
    
    with app.app_context():
        print(f"Creating {num_players} test players...")
        
        # Create one hashed password to reuse (more efficient)
        test_password = generate_password_hash("test123")
        
        for i in range(num_players):
            # Generate fake user data
            username = fake.user_name()
            email = fake.email()
            
            # Generate random battle stats
            wins = random.randint(0, 100)
            losses = random.randint(0, 100)
            
            # Calculate rating based on performance
            total_games = wins + losses
            if total_games > 0:
                win_rate = wins / total_games
                # Base 1000 + bonus for wins - penalty for losses
                rating = int(1000 + (win_rate * 1000) + random.randint(-100, 100))
                # Keep rating within reasonable bounds
                rating = max(600, min(rating, 2000))
            else:
                rating = 600  # Default starting rating
            
            # Random progression stats
            level = random.randint(1, 20)
            xp = random.randint(0, level * 100)
            tokens = random.randint(0, 1000)
            stat_points = random.randint(0, level * 2)
            
            # Create the user
            user = User(
                username=username,
                email=email,
                password=test_password,  # Hashed password
                wins=wins,
                losses=losses,
                rating=rating,
                level=level,
                xp=xp,
                tokens=tokens,
                stat_points=stat_points
            )
            
            db.session.add(user)
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"  Created {i + 1}/{num_players} players...")
        
        # Save all to database
        db.session.commit()
        print(f"✅ Successfully created {num_players} test players!")

if __name__ == "__main__":
    create_test_players(100)
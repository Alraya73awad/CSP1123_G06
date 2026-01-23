from app import app, db, User

def delete_test_players():
    """Removes all test players"""
    
    with app.app_context():
        confirm = input("Are you sure you want to delete ALL users? (yes/no): ")
        
        if confirm.lower() == 'yes':
            deleted = User.query.delete()
            db.session.commit()
            print(f"✅ Deleted {deleted} users")
        else:
            print("❌ Cancelled")

if __name__ == "__main__":
    delete_test_players()
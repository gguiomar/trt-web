import os
import sqlite3

# Connect to the database
db_path = os.path.join('logs', 'users.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the display_name column exists
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]
print("Current columns:", column_names)

# Add the display_name column if it doesn't exist
if 'display_name' not in column_names:
    print("Adding display_name column...")
    cursor.execute("ALTER TABLE users ADD COLUMN display_name TEXT DEFAULT NULL")
    conn.commit()
    print("display_name column added successfully")
else:
    print("display_name column already exists")

# Add the persistent_token column if it doesn't exist
if 'persistent_token' not in column_names:
    print("Adding persistent_token column...")
    cursor.execute("ALTER TABLE users ADD COLUMN persistent_token TEXT DEFAULT NULL")
    conn.commit()
    print("persistent_token column added successfully")
else:
    print("persistent_token column already exists")

# Update all users to have a default display_name if it's NULL
cursor.execute("UPDATE users SET display_name = 'Player_' || substr(user_id, -6) WHERE display_name IS NULL")
conn.commit()
print("Updated users with default display_name")

# Verify the changes
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
print("\nUpdated table columns:")
for column in columns:
    print(column)

# Check all users
cursor.execute("SELECT user_id, display_name FROM users")
all_users = cursor.fetchall()
print("\nAll users:")
for user in all_users:
    print(user)

conn.close()

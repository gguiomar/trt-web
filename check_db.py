import os
import sqlite3

# Connect to the database
db_path = os.path.join('logs', 'users.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the display_name column exists
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
print("Table columns:")
for column in columns:
    print(column)

# Check if there are any users with NULL display_name
cursor.execute("SELECT user_id, display_name FROM users WHERE display_name IS NULL")
null_display_names = cursor.fetchall()
print("\nUsers with NULL display_name:")
for user in null_display_names:
    print(user)

# Check if there are any users with empty string display_name
cursor.execute("SELECT user_id, display_name FROM users WHERE display_name = ''")
empty_display_names = cursor.fetchall()
print("\nUsers with empty string display_name:")
for user in empty_display_names:
    print(user)

# Check all users
cursor.execute("SELECT user_id, display_name FROM users")
all_users = cursor.fetchall()
print("\nAll users:")
for user in all_users:
    print(user)

conn.close()

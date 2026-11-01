import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("college.db")

name = "College Admin"
email = "admin@gmail.com"
password = "admin123"

hashed_password = generate_password_hash(password)

conn.execute(
    "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
    (name, email, hashed_password, "admin")
)

conn.commit()
conn.close()

print("Admin account created successfully!")
print("Email: admin@gmail.com")
print("Password: admin123")
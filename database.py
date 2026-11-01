import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = "college.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # =========================
    # USERS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student'
        )
    """)

    # =========================
    # FAQ TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    """)

    # =========================
    # NOTICES TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add extra notice columns if they don't exist
    columns = cursor.execute(
        "PRAGMA table_info(notices)"
    ).fetchall()

    column_names = [column[1] for column in columns]

    if "category" not in column_names:
        cursor.execute(
            "ALTER TABLE notices ADD COLUMN category TEXT DEFAULT 'General'"
        )

    if "is_important" not in column_names:
        cursor.execute(
            "ALTER TABLE notices ADD COLUMN is_important INTEGER DEFAULT 0"
        )

    # =========================
    # EVENTS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            description TEXT
        )
    """)

    # =========================
    # STUDENT QUESTIONS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question TEXT NOT NULL,
            answer TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # =========================
    # ATTENDANCE TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            attendance_date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES users(id)
        )
    """)

    # =========================
    # CREATE ADMIN
    # =========================
    admin = cursor.execute(
        "SELECT * FROM users WHERE email = ?",
        ("admin@college.com",)
    ).fetchone()

    if not admin:
        cursor.execute("""
            INSERT INTO users
            (name, email, password, role)
            VALUES (?, ?, ?, ?)
        """, (
            "College Admin",
            "admin@college.com",
            generate_password_hash("admin123"),
            "admin"
        ))

    # =========================
    # DEFAULT FAQs
    # =========================
    if cursor.execute(
        "SELECT COUNT(*) FROM faqs"
    ).fetchone()[0] == 0:

        faqs = [
            (
                "What is BCA?",
                "BCA stands for Bachelor of Computer Applications."
            ),
            (
                "What is Python?",
                "Python is a programming language used in AI, automation and web development."
            ),
            (
                "When are exams?",
                "Please check the latest examination notice."
            ),
            (
                "What is attendance requirement?",
                "Please maintain the minimum attendance required by your college."
            )
        ]

        cursor.executemany(
            "INSERT INTO faqs(question, answer) VALUES (?, ?)",
            faqs
        )

    # Save everything
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
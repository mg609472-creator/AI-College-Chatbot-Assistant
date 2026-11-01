from flask import Flask, render_template, request, jsonify ,redirect, url_for, session, flash
from database import init_db, get_db
from werkzeug.security import generate_password_hash,check_password_hash
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

app = Flask(__name__)

app.secret_key =os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

# Initialize database
init_db()


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    conn.close()

    if user and check_password_hash(user["password"], password):
        session["user_id"] = user["id"]
        session["name"] = user["name"]
        session["role"] = user["role"]

        flash("Login successful! 🎉")
        return redirect(url_for("home"))

    flash("Invalid email or password.")
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        flash("Please login first.")
        return redirect(url_for("login"))
    if session.get("role") == "admin":
        return redirect(url_for("admin"))

    conn = get_db()

    notices = conn.execute(
        "SELECT * FROM notices ORDER BY created_at DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        name=session.get("name"),
        notices=notices
    )
@app.route("/chatbot")
def chatbot():
    if not session.get("user_id"):
        flash("Please login first.")
        return redirect(url_for("login"))

    return render_template("chatbot.html")

@app.route("/study-planner")
def study_planner():
    return render_template("study_planner.html")
@app.route("/quiz")
def quiz():
    return render_template("quiz.html")
@app.route("/generate-quiz", methods=["POST"])
def generate_quiz():

    data = request.get_json()

    subject = data.get("subject", "").strip()
    topic = data.get("topic", "").strip()
    difficulty = data.get("difficulty", "").strip()

    if not subject or not topic or not difficulty:
        return jsonify({
            "error": "Please fill all quiz fields."
        }), 400

    prompt = f"""
Create a college-level MCQ quiz for a BCA student.

Subject: {subject}
Topic: {topic}
Difficulty: {difficulty}

Create exactly 10 multiple-choice questions.

Each question must have exactly 4 options.

Return ONLY valid JSON.
Do not use markdown.

Use this format:

{{
  "questions": [
    {{
      "question": "Question text",
      "options": [
        "Option 1",
        "Option 2",
        "Option 3",
        "Option 4"
      ],
      "answer": "Correct option text"
    }}
  ]
}}

The answer must exactly match one of the four options.
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI college quiz generator. Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        quiz_text = response.choices[0].message.content.strip()

        if quiz_text.startswith("```"):
            quiz_text = quiz_text.replace("```json", "")
            quiz_text = quiz_text.replace("```", "")
            quiz_text = quiz_text.strip()

        import json

        quiz_data = json.loads(quiz_text)

        return jsonify(quiz_data)

    except Exception as e:

        print("QUIZ ERROR:", e)

        return jsonify({
            "error": "Quiz could not be generated. Please try again."
        }), 500


@app.route("/notices")
def notices():
    if not session.get("user_id"):
        flash("Please login first.")
        return redirect(url_for("login"))

    conn = get_db()

    notices = conn.execute(
        "SELECT * FROM notices ORDER BY created_at DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "notices.html",
        notices=notices
    )
@app.route("/add-notice", methods=["POST"])
def add_notice():

    # Login check
    if not session.get("user_id"):
        flash("Please login first.")
        return redirect(url_for("login"))

    # Admin check
    if session.get("role") != "admin":
        flash("Only admin can add notices.")
        return redirect(url_for("notices"))

    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    category = request.form.get("category", "General")
    is_important = 1 if request.form.get("is_important") else 0

    if not title or not content:
        flash("Please fill all notice fields.")
        return redirect(url_for("notices"))

    conn = get_db()

    conn.execute(
        """
        INSERT INTO notices
        (title, content, category, is_important)
        VALUES (?, ?, ?, ?)
        """,
        (title, content, category, is_important)
    )

    conn.commit()
    conn.close()

    flash("Notice added successfully! 📢")

    return redirect(url_for("notices"))
@app.route("/delete-notice/<int:notice_id>", methods=["POST"])
def delete_notice(notice_id):

    if not session.get("user_id"):
        flash("Please login first.")
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute(
        "DELETE FROM notices WHERE id = ?",
        (notice_id,)
    )

    conn.commit()
    conn.close()

    flash("Notice deleted successfully!")

    return redirect(url_for("notices"))
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "GET":
        return render_template("admin_login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE email = ? AND role = 'admin'",
        (email,)
    ).fetchone()

    conn.close()

    if user and check_password_hash(user["password"], password):

        session["user_id"] = user["id"]
        session["name"] = user["name"]
        session["role"] = "admin"

        flash("Admin login successful! 👨‍💼")
        return redirect(url_for("admin"))

    flash("Invalid admin email or password.")
    return redirect(url_for("admin_login"))
@app.route("/admin", methods=["GET", "POST"])
def admin():

    if not session.get("user_id"):
        flash("Please login first.")
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("Admin access required.")
        return redirect(url_for("dashboard"))

    conn = get_db()

    # Add Notice
    if request.method == "POST":

        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        if not title or not content:
            flash("Please fill all fields.")
            conn.close()
            return redirect(url_for("admin"))

        conn.execute(
            "INSERT INTO notices (title, content) VALUES (?, ?)",
            (title, content)
        )

        conn.commit()

        flash("Notice added successfully! 📢")

    # Dashboard Statistics
    total_students = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='student'"
    ).fetchone()[0]

    total_notices = conn.execute(
        "SELECT COUNT(*) FROM notices"
    ).fetchone()[0]

    total_attendance = conn.execute(
        "SELECT COUNT(*) FROM attendance"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        total_students=total_students,
        total_notices=total_notices,
        total_attendance=total_attendance
    )
# =========================
# ADMIN ATTENDANCE
# =========================

@app.route("/attendance", methods=["GET", "POST"])
def attendance():

    # Login check
    if not session.get("user_id"):
        flash("Please login first.")
        return redirect(url_for("login"))

    # Admin check
    if session.get("role") != "admin":
        flash("Admin access required.")
        return redirect(url_for("dashboard"))

    conn = get_db()

    # Attendance save
    if request.method == "POST":

        student_id = request.form.get("student_id")
        attendance_date = request.form.get("attendance_date")
        status = request.form.get("status")

        if not student_id or not attendance_date or not status:
            conn.close()
            flash("Please fill all attendance fields.")
            return redirect(url_for("attendance"))

        # Check if attendance already exists
        existing = conn.execute(
            """
            SELECT id FROM attendance
            WHERE student_id = ? AND attendance_date = ?
            """,
            (student_id, attendance_date)
        ).fetchone()

        if existing:
            # Update existing attendance
            conn.execute(
                """
                UPDATE attendance
                SET status = ?
                WHERE id = ?
                """,
                (status, existing["id"])
            )

            flash("Attendance updated successfully! ✅")

        else:
            # Add new attendance
            conn.execute(
                """
                INSERT INTO attendance
                (student_id, attendance_date, status)
                VALUES (?, ?, ?)
                """,
                (student_id, attendance_date, status)
            )

            flash("Attendance added successfully! ✅")

        conn.commit()

    # Get all students
    students = conn.execute(
        """
        SELECT id, name, email
        FROM users
        WHERE role = 'student'
        ORDER BY name
        """
    ).fetchall()

    # Get attendance records
    attendance_records = conn.execute(
        """
        SELECT
            attendance.id,
            users.name,
            users.email,
            attendance.attendance_date,
            attendance.status
        FROM attendance
        JOIN users
        ON attendance.student_id = users.id
        ORDER BY attendance.attendance_date DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "attendance.html",
        students=students,
        attendance_records=attendance_records
    )
# =========================
# STUDENT MY ATTENDANCE
# =========================

@app.route("/my-attendance")
def my_attendance():

    if not session.get("user_id"):
        flash("Please login first.")
        return redirect(url_for("login"))

    if session.get("role") != "student":
        flash("Student access required.")
        return redirect(url_for("admin"))

    conn = get_db()

    records = conn.execute(
        """
        SELECT attendance_date, status
        FROM attendance
        WHERE student_id = ?
        ORDER BY attendance_date DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "my_attendance.html",
        records=records
    )
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not name or not email or not password:
        flash("Please fill all fields.")
        return redirect(url_for("register"))

    conn = get_db()

    existing_user = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if existing_user:
        conn.close()
        flash("Email already registered.")
        return redirect(url_for("register"))

    hashed_password = generate_password_hash(password)

    conn.execute(
        "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
        (name, email, hashed_password, "student")
    )

    conn.commit()
    conn.close()

    flash("Registration successful! Please login.")
    return redirect(url_for("login"))

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()

    user_text = data.get("question", "").strip()
    task = data.get("task", "general")

    if not user_text:
        return jsonify({"error": "Please enter some text!"}), 400

    try:
        prompt = f"""
You are an AI College Assistant.

Answer the student's question clearly and helpfully.
Focus on college, BCA, academics, admissions, exams, projects,
programming, technology, and student-related questions.

Student question:
{user_text}
"""

        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        answer = response.choices[0].message.content

        return jsonify({
            "response": answer
        })

    except Exception as e:
        print("API ERROR:", e)
        return jsonify({
            "error": str(e)
        }), 503


if __name__ == "__main__":
    app.run(debug=True)
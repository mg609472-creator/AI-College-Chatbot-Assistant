import sqlite3
import re

DATABASE = "college.db"

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    return text

def chatbot_response(message):
    message = clean_text(message)

    if any(word in message.split() for word in ["hello", "hi", "hey"]):
        return "Hello! 👋 I am your AI College Assistant. How can I help you?"

    if "bye" in message:
        return "Goodbye! 👋 Have a great day."

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    faqs = cursor.execute(
        "SELECT question, answer FROM faqs"
    ).fetchall()

    conn.close()

    best_answer = None
    best_score = 0

    for question, answer in faqs:
        question_words = set(clean_text(question).split())
        message_words = set(message.split())

        common_words = question_words.intersection(message_words)
        score = len(common_words)

        if score > best_score:
            best_score = score
            best_answer = answer

    if best_score >= 1:
        return best_answer

    if "python" in message:
        return "Python is a popular programming language used in AI, automation and web development."

    if "exam" in message:
        return "For examination information, please check the latest college notice."

    if "fee" in message:
        return "For current fee information, please contact the college administration."

    if "assignment" in message:
        return "You can check your assignment information from the dashboard."

    if "study" in message:
        return "I recommend studying in small sessions and revising important topics regularly."

    return "I'm not sure about that yet. Try asking about BCA, exams, fees, Python, assignments or attendance."
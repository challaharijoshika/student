# 

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "super_secret_key"

DATABASE = "database.db"


# ---------------- DATABASE ---------------- #

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            rollNo TEXT PRIMARY KEY,
            name TEXT,
            marks TEXT,
            totalMarks INTEGER,
            percentage REAL,
            grade TEXT
        )
    """)

    # Default admin account
    cursor.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", "admin123", "admin")
        )

    conn.commit()
    conn.close()


# ---------------- HELPERS ---------------- #

def calculate_results(marks):
    total = sum(marks)
    percentage = total / (len(marks) * 100) * 100

    if percentage >= 90:
        grade = "A+"
    elif percentage >= 80:
        grade = "A"
    elif percentage >= 70:
        grade = "B"
    elif percentage >= 60:
        grade = "C"
    elif percentage >= 50:
        grade = "D"
    else:
        grade = "F"

    return total, percentage, grade


def is_admin():
    return session.get("role") == "admin"


# ---------------- ROUTES ---------------- #

# ⭐ LANDING PAGE (NEW)
@app.route("/")
def home():
    return render_template("home.html")


# ---------------- AUTH ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password),
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ---------------- ADMIN DASHBOARD ---------------- #

@app.route("/dashboard")
def dashboard():
    if not is_admin():
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    conn.close()

    return render_template("dashboard.html", students=students)


@app.route("/add", methods=["GET", "POST"])
def add_student():
    if not is_admin():
        return redirect(url_for("login"))

    if request.method == "POST":
        rollNo = request.form["rollNo"]
        name = request.form["name"]
        marks = list(map(int, request.form["marks"].split(",")))

        total, percentage, grade = calculate_results(marks)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO students VALUES (?, ?, ?, ?, ?, ?)",
            (rollNo, name, ",".join(map(str, marks)), total, percentage, grade),
        )
        conn.commit()
        conn.close()

        flash("Student added successfully")
        return redirect(url_for("dashboard"))

    return render_template("add_edit.html", mode="add")


@app.route("/edit/<rollNo>", methods=["GET", "POST"])
def edit_student(rollNo):
    if not is_admin():
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        marks = list(map(int, request.form["marks"].split(",")))
        total, percentage, grade = calculate_results(marks)

        cursor.execute("""
            UPDATE students
            SET name=?, marks=?, totalMarks=?, percentage=?, grade=?
            WHERE rollNo=?
        """, (name, ",".join(map(str, marks)), total, percentage, grade, rollNo))

        conn.commit()
        conn.close()
        flash("Student updated successfully")
        return redirect(url_for("dashboard"))

    cursor.execute("SELECT * FROM students WHERE rollNo=?", (rollNo,))
    student = cursor.fetchone()
    conn.close()

    return render_template("add_edit.html", mode="edit", student=student)


@app.route("/delete/<rollNo>")
def delete_student(rollNo):
    if not is_admin():
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE rollNo=?", (rollNo,))
    conn.commit()
    conn.close()

    flash("Student deleted")
    return redirect(url_for("dashboard"))


# ---------------- STUDENT SEARCH ---------------- #

@app.route("/search", methods=["GET", "POST"])
def search_student():
    student = None

    if request.method == "POST":
        rollNo = request.form["rollNo"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE rollNo=?", (rollNo,))
        student = cursor.fetchone()
        conn.close()

    return render_template("search.html", student=student)


# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    init_db()
    app.run(debug=True)



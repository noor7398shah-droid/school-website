from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = "school_secret_key"

DB_NAME = "database.db"

# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        class TEXT,
        phone TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        subject TEXT,
        phone TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        status TEXT,
        date TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS fees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        amount INTEGER,
        status TEXT,
        date TEXT
    )
    """)

    conn.commit()
    return conn

# ---------- BASIC PAGES ----------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

# ---------- ADMISSION ----------
@app.route("/admission", methods=["GET", "POST"])
def admission():
    if request.method == "POST":
        db = get_db()
        db.execute(
            "INSERT INTO students (name, class, phone) VALUES (?, ?, ?)",
            (request.form["name"], request.form["class"], request.form["phone"])
        )
        db.commit()
        db.close()
        return redirect("/")
    return render_template("admission.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin":
            session["admin"] = True
            return redirect("/admin")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------- ADMIN ----------
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")
    db = get_db()
    students = db.execute("SELECT * FROM students").fetchall()
    db.close()
    return render_template("admin.html", students=students)

# ---------- TEACHERS ----------
@app.route("/teachers")
def teachers():
    if not session.get("admin"):
        return redirect("/login")
    db = get_db()
    data = db.execute("SELECT * FROM teachers").fetchall()
    db.close()
    return render_template("teacher_list.html", teachers=data)

@app.route("/teacher/add", methods=["GET", "POST"])
def teacher_add():
    if not session.get("admin"):
        return redirect("/login")
    if request.method == "POST":
        db = get_db()
        db.execute(
            "INSERT INTO teachers (name, subject, phone) VALUES (?, ?, ?)",
            (request.form["name"], request.form["subject"], request.form["phone"])
        )
        db.commit()
        db.close()
        return redirect("/teachers")
    return render_template("teacher_add.html")

@app.route("/teacher/delete/<int:id>")
def teacher_delete(id):
    if not session.get("admin"):
        return redirect("/login")
    db = get_db()
    db.execute("DELETE FROM teachers WHERE id=?", (id,))
    db.commit()
    db.close()
    return redirect("/teachers")

# ---------- ATTENDANCE ----------
@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    if not session.get("admin"):
        return redirect("/login")

    today = str(date.today())
    db = get_db()

    if request.method == "POST":
        for key, value in request.form.items():
            if key.startswith("student_"):
                student_id = key.split("_")[1]
                db.execute(
                    "INSERT INTO attendance (student_id, status, date) VALUES (?, ?, ?)",
                    (student_id, value, today)
                )
        db.commit()
        db.close()
        return redirect("/attendance/list")

    students = db.execute("SELECT * FROM students").fetchall()
    db.close()
    return render_template("attendance_mark.html", students=students, today=today)

@app.route("/attendance/list")
def attendance_list():
    if not session.get("admin"):
        return redirect("/login")
    db = get_db()
    data = db.execute("""
        SELECT students.name, students.class, attendance.status, attendance.date
        FROM attendance
        JOIN students ON students.id = attendance.student_id
        ORDER BY attendance.date DESC
    """).fetchall()
    db.close()
    return render_template("attendance_list.html", records=data)

# ---------- FEES ----------
@app.route("/fees/add", methods=["GET", "POST"])
def fees_add():
    if not session.get("admin"):
        return redirect("/login")

    db = get_db()

    if request.method == "POST":
        db.execute(
            "INSERT INTO fees (student_id, amount, status, date) VALUES (?, ?, ?, ?)",
            (
                request.form["student_id"],
                request.form["amount"],
                request.form["status"],
                str(date.today())
            )
        )
        db.commit()
        db.close()
        return redirect("/fees")

    students = db.execute("SELECT * FROM students").fetchall()
    db.close()
    return render_template("fees_add.html", students=students)

@app.route("/fees")
def fees_list():
    if not session.get("admin"):
        return redirect("/login")

    db = get_db()
    data = db.execute("""
        SELECT students.name, students.class, fees.amount, fees.status, fees.date
        FROM fees
        JOIN students ON students.id = fees.student_id
        ORDER BY fees.date DESC
    """).fetchall()
    db.close()

    return render_template("fees_list.html", records=data)

@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")

    db = get_db()

    # Students per class
    students = db.execute("""
        SELECT class, COUNT(*) FROM students GROUP BY class
    """).fetchall()

    # Fees paid vs due
    fees = db.execute("""
        SELECT status, COUNT(*) FROM fees GROUP BY status
    """).fetchall()

    # Attendance summary (example static %)
    attendance = {
        "Present": 85,
        "Absent": 15
    }

    db.close()

    return render_template(
        "dashboard.html",
        students=students,
        fees=fees,
        attendance=attendance
    )


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

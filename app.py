from flask import Flask, render_template, request, redirect, session
import models
import PyPDF2
import docx
import json
from db import Base, engine, SessionLocal

app = Flask(__name__)
app.secret_key = "secretkey123"

Base.metadata.create_all(bind=engine)


# homepage route
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")


# sign up route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    db = SessionLocal()
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = db.query(models.User).filter_by(email=email).first()
        if existing_user:
            return "User already exists"

        new_user = models.User(email=email, password=password)
        db.add(new_user)
        db.commit()
        return redirect("/login")
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    db = SessionLocal()
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = db.query(models.User).filter_by(email=email, password=password).first()
        if user:
            session["user"] = user.email
            return redirect("/dashboard")
        else:
            return "Invalid credentials"
    return render_template("login.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    result = None
    user_goal = None
    resume_text = None

    if request.method == "POST":
        user_goal = request.form.get("role")
        resume_text = request.form.get("resume")
        file = request.files.get("file")

        # 1. File Handling (PDF/DOCX)
        if file and file.filename != "":
            if file.filename.endswith(".pdf"):
                try:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""
                    resume_text = text
                except Exception as e:
                    result = {"error": f"pdf error: {str(e)}"}
            elif file.filename.endswith(".docx"):
                try:
                    doc = docx.Document(file)
                    text = "\n".join([para.text for para in doc.paragraphs])
                    resume_text = text
                except Exception as e:
                    result = {"error": f"Docx error: {str(e)}"}

        # 2. Trigger AI Analysis
        if resume_text and user_goal:
            try:
                result = analyze_resume(resume_text, user_goal)

                # 3. Save to Database
                db = SessionLocal()
                user = db.query(models.User).filter_by(email=session["user"]).first()

                report = models.Report(
                    user_id=user.id,
                    resume_text=resume_text,
                    result=json.dumps(result),  # Store as string
                )
                db.add(report)
                db.commit()
                db.close()
            except Exception as e:
                result = {"error": f"Analysis error: {str(e)}"}

    return render_template("dashboard.html", user=session["user"], result=result)


@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    db = SessionLocal()
    user = db.query(models.User).filter_by(email=session["user"]).first()
    # Fetch reports for this specific user
    reports = db.query(models.Report).filter_by(user_id=user.id).all()

    for r in reports:
        try:
            # Decode string back to dict
            r.result_json = json.loads(r.result)
        except:
            r.result_json = {"feedback": "Error loading report"}

    db.close()
    return render_template("history.html", reports=reports)


# logout route
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)

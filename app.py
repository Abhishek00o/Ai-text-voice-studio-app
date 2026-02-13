from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from gtts import gTTS
from googletrans import Translator
from PyPDF2 import PdfReader
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

translator = Translator()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        user = User(username=request.form["username"],
                    password=request.form["password"])
        db.session.add(user)
        db.session.commit()
        flash("Registered Successfully")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()
        if user:
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid Credentials")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/convert", methods=["POST"])
@login_required
def convert():
    text = request.form["text"]
    lang = request.form["language"]
    tts = gTTS(text=text, lang=lang)
    filename = "static/output.mp3"
    tts.save(filename)
    return send_file(filename, as_attachment=True)

@app.route("/translate", methods=["POST"])
@login_required
def translate():
    text = request.form["text"]
    lang = request.form["language"]
    translated = translator.translate(text, dest=lang)
    flash("Translated Text: " + translated.text)
    return redirect(url_for("dashboard"))

@app.route("/pdf", methods=["POST"])
@login_required
def pdf_to_speech():
    file = request.files["pdf"]
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    tts = gTTS(text=text, lang="en")
    filename = "static/pdf_audio.mp3"
    tts.save(filename)
    return send_file(filename, as_attachment=True)

@app.route("/admin")
@login_required
def admin():
    if not current_user.is_admin:
        return "Access Denied"
    users = User.query.all()
    return render_template("admin.html", users=users)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
    
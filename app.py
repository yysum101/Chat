import os
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# --- App setup ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")

# Database setup
db_url = os.environ.get("DATABASE_URL", "sqlite:///chat.db")
db_url = db_url.replace("postgres://", "postgresql://")  # fix for NeonDB
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    about = db.Column(db.String(500), default="")
    messages = db.relationship("Message", backref="user", lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- Helpers ---
def get_current_user():
    if "user_id" in session:
        return User.query.get(session["user_id"])
    return None

def login_required(f):
    def wrapper(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# --- Template wrapper ---
def render_page(title, content):
    base_template = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} • Chatterbox</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body { background: linear-gradient(to right, #1abc9c, #3498db); min-height:100vh; }
.navbar { background-color: rgba(0,0,0,0.8) !important; }
.card { background-color: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
.chat-container { max-height:400px; overflow-y:auto; display:flex; flex-direction:column; gap:8px; margin-bottom:10px; }
.chat-bubble { padding:10px 15px; border-radius:15px; max-width:70%; }
.chat-me { background-color:#34d399; align-self:flex-end; color:white; }
.chat-other { background-color:#3b82f6; align-self:flex-start; color:white; }
.small-text { font-size:0.7rem; color:#eee; margin-top:2px; }
</style>
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark">
  <div class="container">
    <a class="navbar-brand" href="{{ url_for('index') }}">Chatterbox</a>
    <div>
      {% if current_user %}
        <a href="{{ url_for('chat') }}" class="btn btn-success btn-sm">Chat</a>
        <a href="{{ url_for('profile', username=current_user.username) }}" class="btn btn-info btn-sm">Profile</a>
        <a href="{{ url_for('logout') }}" class="btn btn-danger btn-sm">Logout</a>
      {% else %}
        <a href="{{ url_for('login') }}" class="btn btn-primary btn-sm">Login</a>
        <a href="{{ url_for('register') }}" class="btn btn-warning btn-sm">Register</a>
      {% endif %}
    </div>
  </div>
</nav>
<div class="container py-4">
{{ content|safe }}
</div>
</body>
</html>
"""
    return render_template_string(base_template, title=title, current_user=get_current_user(), content=content)

# --- Routes ---
@app.route("/")
def index():
    if get_current_user():
        return redirect(url_for("chat"))
    return render_page("Home", """
    <div class="text-center text-white">
      <h1 class="mb-4">Welcome to Chatterbox</h1>
      <p class="lead">Login or register to start chatting!</p>
      <a href="{{ url_for('login') }}" class="btn btn-primary">Login</a>
      <a href="{{ url_for('register') }}" class="btn btn-warning">Register</a>
    </div>
    """)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        confirm = request.form["confirm"]
        about_me = request.form["about"].strip()
        if password != confirm:
            return render_page("Register", "<p class='text-danger'>Passwords do not match!</p>")
        if User.query.filter_by(username=username).first():
            return render_page("Register", "<p class='text-danger'>Username already exists!</p>")
        user = User(username=username,
                    password_hash=generate_password_hash(password),
                    about=about_me)
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        return redirect(url_for("chat"))
    return render_page("Register", """
    <div class="card p-4 mx-auto" style="max-width:400px;">
      <h3 class="mb-3">Register</h3>
      <form method="POST">
        <input name="username" class="form-control mb-2" placeholder="Username" required>
        <input type="password" name="password" class="form-control mb-2" placeholder="Password" required>
        <input type="password" name="confirm" class="form-control mb-2" placeholder="Confirm Password" required>
        <textarea name="about" class="form-control mb-2" placeholder="About me..."></textarea>
        <button class="btn btn-success w-100">Register</button>
      </form>
    </div>
    """)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash, password):
            return render_page("Login", "<p class='text-danger'>Invalid credentials!</p>")
        session["user_id"] = user.id
        return redirect(url_for("chat"))
    return render_page("Login", """
    <div class="card p-4 mx-auto" style="max-width:400px;">
      <h3 class="mb-3">Login</h3>
      <form method="POST">
        <input name="username" class="form-control mb-2" placeholder="Username" required>
        <input type="password" name="password" class="form-control mb-2" placeholder="Password" required>
        <button class="btn btn-primary w-100">Login</button>
      </form>
    </div>
    """)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    if request.method == "POST":
        subject = request.form["subject"].strip()
        content = request.form["content"].strip()
        if subject and content:
            msg = Message(user_id=get_current_user().id, subject=subject, content=content)
            db.session.add(msg)
            db.session.commit()
        return redirect(url_for("chat"))

    messages_html = ""
    messages = Message.query.order_by(Message.created_at.asc()).all()
    for m in messages:
        if m.user_id == get_current_user().id:
            messages_html += f"""
            <div class="chat-bubble chat-me">
                <strong>{m.subject}</strong><br>{m.content}
                <div class="small-text">{m.created_at.strftime('%H:%M')}</div>
            </div>"""
        else:
            messages_html += f"""
            <div class="chat-bubble chat-other">
                <strong>{m.user.username} - {m.subject}</strong><br>{m.content}
                <div class="small-text">{m.created_at.strftime('%H:%M')}</div>
            </div>"""

    return render_page("Chat", f"""
    <h4 class="text-white">Chat Room</h4>
    <a href="{{{{ url_for('index') }}}}" class="btn btn-light btn-sm mb-3">🏠 Home</a>
    <div class="chat-container">{messages_html}</div>
    <form method="POST">
        <input name="subject" class="form-control mb-2" placeholder="Subject" required>
        <textarea name="content" class="form-control mb-2" placeholder="Message body..." required></textarea>
        <button class="btn btn-success w-100">Send</button>
    </form>
    """)

@app.route("/profile/<username>")
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_page(f"{user.username}'s Profile", f"""
    <div class="card p-4">
      <a href="{{{{ url_for('index') }}}}" class="btn btn-light btn-sm mb-3">🏠 Home</a>
      <h3>{user.username}</h3>
      <p>{user.about or "No bio yet."}</p>
    </div>
    """)

# --- Initialize DB ---
with app.app_context():
    db.create_all()

# --- Run ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

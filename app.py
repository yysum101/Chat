# ---------- Flask Config ----------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///chat.db").replace("postgres://", "postgresql://")

# Database: Prefer NeonDB (Postgres), fallback to SQLite
db_url = os.environ.get("DATABASE_URL", "sqlite:///chat.db")
# NeonDB URLs often start with postgres:// but SQLAlchemy needs postgresql://
db_url = db_url.replace("postgres://", "postgresql://")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

@@ -48,7 +53,7 @@
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }}</title>
<title>{{ title }} • Chatterbox</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
:root{ --bg1:#0ea5a1; --bg2:#1d4ed8; }
@@ -60,7 +65,7 @@
<body>
<nav class="navbar navbar-expand-lg navbar-dark">
 <div class="container">
    <a class="navbar-brand" href="{{ url_for('index') }}">BlueGreen Chat</a>
    <a class="navbar-brand" href="{{ url_for('index') }}">Chatterbox</a>
   <div class="ms-auto">
     {% if cu %}
       <a href="{{ url_for('profile', username=cu.username) }}" class="text-white me-3">{{ cu.username }}</a>
@@ -89,104 +94,104 @@
if current_user():
return redirect(url_for("chat"))
return render_page("Home", f"""
    <h1>Welcome to BlueGreen Chat</h1>
    <h1>Welcome to Chatterbox</h1>
   <p>Please login or register to chat.</p>
   <a href="{url_for('login')}" class="btn btn-primary">Login</a>
   <a href="{url_for('register')}" class="btn btn-secondary">Register</a>
   """)

@app.route("/register", methods=["GET","POST"])
def register():
if current_user():
return redirect(url_for("chat"))
if request.method == "POST":
username = request.form["username"].strip()
pw = request.form["password"]
pw2 = request.form["confirm"]
about = request.form.get("about","").strip()
if not username or not pw or not pw2:
flash("Fill all required fields")
elif pw != pw2:
flash("Passwords do not match")
elif User.query.filter_by(username=username).first():
flash("Username taken")
else:
u = User(username=username, about=about)
u.set_password(pw)
db.session.add(u)
db.session.commit()
flash("Registered! Please login.")
return redirect(url_for("login"))
return render_page("Register", f"""
   <h2>Create Account</h2>
   <form method="post">
     <div class="mb-3"><label>Username</label><input name="username" class="form-control" required></div>
     <div class="mb-3"><label>About myself</label><input name="about" class="form-control"></div>
     <div class="mb-3"><label>Password</label><input type="password" name="password" class="form-control" required></div>
     <div class="mb-3"><label>Confirm Password</label><input type="password" name="confirm" class="form-control" required></div>
     <button class="btn btn-primary">Register</button>
   </form>""")

@app.route("/login", methods=["GET","POST"])
def login():
if current_user():
return redirect(url_for("chat"))
if request.method == "POST":
username = request.form["username"]
pw = request.form["password"]
u = User.query.filter_by(username=username).first()
if u and u.check_password(pw):
session["uid"] = u.id
return redirect(url_for("chat"))
else:
flash("Invalid login")
return render_page("Login", f"""
   <h2>Login</h2>
   <form method="post">
     <div class="mb-3"><label>Username</label><input name="username" class="form-control" required></div>
     <div class="mb-3"><label>Password</label><input type="password" name="password" class="form-control" required></div>
     <button class="btn btn-primary">Login</button>
   </form>""")

@app.route("/logout")
def logout():
session.clear()
return redirect(url_for("index"))

@app.route("/chat", methods=["GET","POST"])
def chat():
if not current_user():
return redirect(url_for("login"))
if request.method == "POST":
msg = request.form.get("message","").strip()
if msg:
m = Message(user_id=current_user().id, content=msg)
db.session.add(m)
db.session.commit()
return redirect(url_for("chat"))
msgs = Message.query.order_by(Message.created_at.desc()).limit(20).all()
messages_html = "".join(
f"<div class='mb-2'><strong><a href='{url_for('profile', username=m.author.username)}'>{m.author.username}</a>:</strong> {m.content} <small class='text-muted'>{m.created_at.strftime('%H:%M')}</small></div>"
for m in reversed(msgs)
)
return render_page("Chat", f"""
   <h2>Chat Room</h2>
   <div class="mb-3" style="max-height:300px;overflow:auto;">{messages_html}</div>
   <form method="post" class="d-flex">
     <input name="message" class="form-control me-2" placeholder="Type a message..." required>
     <button class="btn btn-primary">Send</button>
   </form>
   """)

@app.route("/profile/<username>")
def profile(username):
if not current_user():
return redirect(url_for("login"))
u = User.query.filter_by(username=username).first_or_404()
return render_page(f"{u.username}'s Profile", f"""
   <h2>{u.username}</h2>
   <p><strong>About:</strong> {u.about or 'No info'}</p>
   """)

if __name__ == "__main__":
app.run(host="0.0.0.0", port=5000)

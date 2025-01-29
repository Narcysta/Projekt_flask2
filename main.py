from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = "secretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class GameResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    winner = db.Column(db.String(10), nullable=False)

game_state = ["" for _ in range(9)]
current_player = "X"
messages = []  

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def check_winner():
    """Check if there is a winner."""
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]

    for combo in winning_combinations:
        if game_state[combo[0]] == game_state[combo[1]] == game_state[combo[2]] != "":
            return game_state[combo[0]]

    if "" not in game_state:
        return "Draw"

    return None

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    global game_state, current_player, messages
    winner = check_winner()

    if request.method == "POST" and not winner:  
        if request.form.get("move"):
            cell = int(request.form["move"])
            if game_state[cell] == "":
                game_state[cell] = current_player
                current_player = "O" if current_player == "X" else "X"

                
                winner = check_winner()
                if winner:
                    db.session.add(GameResult(winner=winner))
                    db.session.commit()

        message = request.form.get("message")
        if message:
            messages.append(message)

    return render_template(
        "index.html",
        game_state=game_state,
        current_player=current_player if not winner else None,  
        winner=winner,
        messages=messages
    )

@app.route("/reset", methods=["POST"])
@login_required
def reset():
    global game_state, current_player
    game_state = ["" for _ in range(9)]
    current_player = "X"
    return redirect(url_for("index"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for("index"))
        else:
            return "Invalid credentials, please try again."

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            return "Username already exists, please choose another."

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


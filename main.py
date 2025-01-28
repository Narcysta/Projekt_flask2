from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "secretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class GameResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    winner = db.Column(db.String(10), nullable=False)

# Initial game state
game_state = ["" for _ in range(9)]  # Empty 3x3 board
current_player = "X"


def check_winner():
    """Check if there is a winner."""
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]              # Diagonals
    ]

    for combo in winning_combinations:
        if game_state[combo[0]] == game_state[combo[1]] == game_state[combo[2]] != "":
            return game_state[combo[0]]
    
    if "" not in game_state:
        return "Draw"

    return None

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    global game_state, current_player
    winner = check_winner()
    if winner and winner != "Draw":
        db.session.add(GameResult(winner=winner))
        db.session.commit()
    return render_template("index.html", game_state=game_state, current_player=current_player, winner=winner)

@app.route("/move/<int:cell>", methods=["POST"])
def move(cell):
    global game_state, current_player

    if game_state[cell] == "" and not check_winner():  # Only allow move if cell is empty and no winner
        game_state[cell] = current_player
        current_player = "O" if current_player == "X" else "X"

    return redirect(url_for("index"))

@app.route("/reset", methods=["POST"])
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
            session["user_id"] = user.id
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
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


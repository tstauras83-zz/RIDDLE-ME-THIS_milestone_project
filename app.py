import json
import os
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, BooleanField
from passlib.hash import sha256_crypt
from functools import wraps


############
###config###
############

app = Flask(__name__)
app.secret_key = os.getenv("SECRET", "randomstring123")





MAX_ATTEMPTS = 3
with open("data/riddles.json") as riddle_file:
    RIDDLES = json.load(riddle_file)

high_score = {
    "name": "nobody",
    "score": 0
}

class RegistrationForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the TOS', [validators.DataRequired()])


    
    



############
###Routes###
############

@app.route("/")
def index():
    return render_template("index.html")
    
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')
    

    
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User(form.username.data, form.email.data,
                    form.password.data)
        db_session.add(user)
        flash('Thanks for registering')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)
    
@app.route("/game_over")
def game_over():
    return render_template("game_over.html")
    
@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")
    
@app.route("/wrong_answers")
def wrong_answers():
    return render_template("wrong_answers.html")
    
@app.route("/new_game", methods=["GET", "POST"])
def new_game():
    session["player"] = request.form["player"]
    session["score"] = 0
    session["riddle_num"] = 0
    session["riddle_attempts"] = MAX_ATTEMPTS
    return redirect(url_for("riddle"))


@app.route("/riddle", methods=["GET", "POST"])
def riddle():
    if "player" not in session:
        return redirect(url_for("login"))

    if request.method == "POST" and session["riddle_num"] < len(RIDDLES):
        previous_riddle = RIDDLES[session["riddle_num"]]
        if request.form["answer"].lower() == previous_riddle["answer"]:
            session["riddle_num"] += 1
            session["score"] += 1
            if session["riddle_num"] < len(RIDDLES):
                flash("Correct answer, %s! Your score is %s." % (
                      session["player"], session["score"]))
            else:
                flash("Correct answer, %s!" % session["player"])
        elif not session["riddle_attempts"]:
            session["riddle_num"] += 1
            session["riddle_attempts"] = MAX_ATTEMPTS
            if session["riddle_num"] < len(RIDDLES):
                flash("Wrong answer, %s. Better luck with this riddle:" % (
                      session["player"]))
        else:
            session["riddle_attempts"] -= 1
            flash("Wrong answer, %s. You have %s attempts left." % (
                  session["player"], session["riddle_attempts"]))

    if session["riddle_num"] >= len(RIDDLES):
        if session["score"] >= high_score["score"]:
            high_score["score"] = session["score"]
            high_score["name"] = session["player"]
        return render_template("game_over.html", player=session["player"],
                               score=session["score"],
                               highscore=high_score["score"],
                               highscorer=high_score["name"])

    new_riddle = RIDDLES[session["riddle_num"]]
    return render_template(
        "riddle.html", player=session["player"],
        question=new_riddle["question"], riddle_num=session["riddle_num"])




#############
###app run###
#############

if __name__ == "__main__":
    app.run(os.getenv("IP", "0.0.0.0"), port=int(os.getenv("PORT", "8080")),
            debug=True)
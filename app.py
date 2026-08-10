from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///farmers.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "agriguide_secret_key"

db = SQLAlchemy(app)


class Farmer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        location = request.form["location"]

        existing_farmer = Farmer.query.filter_by(email=email).first()

        if existing_farmer:
            return "Email already registered. Please use another email."

        farmer = Farmer(
            name=name,
            email=email,
            password=password,
            location=location
        )

        db.session.add(farmer)
        db.session.commit()

        return render_template("success.html")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        farmer = Farmer.query.filter_by(
            email=email,
            password=password
        ).first()

        if farmer:

            session["farmer_id"] = farmer.id
            session["farmer_name"] = farmer.name

            return redirect("/dashboard")

        return "Invalid email or password."


    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "farmer_id" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        name=session["farmer_name"]
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
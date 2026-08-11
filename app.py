from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///farmers.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        location = request.form["location"]

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


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/crop-recommendation", methods=["GET", "POST"])
def crop_recommendation():

    recommendation = None

    if request.method == "POST":

        nitrogen = float(request.form["nitrogen"])
        phosphorus = float(request.form["phosphorus"])
        potassium = float(request.form["potassium"])
        temperature = float(request.form["temperature"])
        humidity = float(request.form["humidity"])
        ph = float(request.form["ph"])
        rainfall = float(request.form["rainfall"])


        # Temporary recommendation logic

        if rainfall > 200 and humidity > 70:
            recommendation = "Rice"

        elif temperature > 25 and rainfall > 100:
            recommendation = "Maize"

        elif ph >= 6 and ph <= 7.5 and rainfall < 100:
            recommendation = "Wheat"

        else:
            recommendation = "Cotton"


    return render_template(
        "crop_recommendation.html",
        recommendation=recommendation
    )


if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.secret_key = "agriguide_secret_key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///farmers.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ==============================
# FARMER DATABASE MODEL
# ==============================

class Farmer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


# ==============================
# CREATE DATABASE
# ==============================

with app.app_context():
    db.create_all()


# ==============================
# HOME / INDEX
# ==============================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/home")
def home():
    return render_template("home.html")


# ==============================
# REGISTER
# ==============================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        existing = Farmer.query.filter_by(email=email).first()

        if existing:
            return "Email already registered"

        farmer = Farmer(
            name=name,
            email=email,
            password=password
        )

        db.session.add(farmer)
        db.session.commit()

        return render_template("success.html", name=name)

    return render_template("register.html")


# ==============================
# LOGIN
# ==============================

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

            session["farmer_name"] = farmer.name

            return redirect(url_for("home"))

        return "Invalid email or password"

    return render_template("login.html")


# ==============================
# DASHBOARD
# ==============================

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ==========================================================
# MODULE 1 - CROP RECOMMENDATION
# ==========================================================

@app.route("/crop-recommendation", methods=["GET", "POST"])
def crop_recommendation():

    crop = None

    if request.method == "POST":

        try:

            nitrogen = float(request.form["nitrogen"])
            phosphorus = float(request.form["phosphorus"])
            potassium = float(request.form["potassium"])
            temperature = float(request.form["temperature"])
            humidity = float(request.form["humidity"])
            ph = float(request.form["ph"])
            rainfall = float(request.form["rainfall"])

            # INPUT VALIDATION

            if nitrogen < 0 or phosphorus < 0 or potassium < 0:
                return render_template(
                    "crop_recommendation.html",
                    crop="Please enter valid N, P and K values."
                )

            if humidity < 0 or humidity > 100:
                return render_template(
                    "crop_recommendation.html",
                    crop="Humidity must be between 0 and 100."
                )

            if ph < 0 or ph > 14:
                return render_template(
                    "crop_recommendation.html",
                    crop="pH must be between 0 and 14."
                )

            if rainfall < 0:
                return render_template(
                    "crop_recommendation.html",
                    crop="Rainfall cannot be negative."
                )

            # CROP SCORES

            scores = {
                "Rice": 0,
                "Wheat": 0,
                "Maize": 0,
                "Cotton": 0,
                "Sugarcane": 0,
                "Groundnut": 0,
                "Millet": 0
            }

            # RICE

            if 20 <= temperature <= 30:
                scores["Rice"] += 2

            if humidity >= 70:
                scores["Rice"] += 2

            if rainfall >= 150:
                scores["Rice"] += 2

            if 5.5 <= ph <= 7.5:
                scores["Rice"] += 1

            if nitrogen >= 70:
                scores["Rice"] += 1

            if phosphorus >= 30:
                scores["Rice"] += 1

            if potassium >= 30:
                scores["Rice"] += 1

            # WHEAT

            if 15 <= temperature <= 25:
                scores["Wheat"] += 2

            if 40 <= humidity <= 70:
                scores["Wheat"] += 2

            if 50 <= rainfall <= 150:
                scores["Wheat"] += 2

            if 5.5 <= ph <= 7.5:
                scores["Wheat"] += 1

            if nitrogen >= 40:
                scores["Wheat"] += 1

            if phosphorus >= 20:
                scores["Wheat"] += 1

            if potassium >= 20:
                scores["Wheat"] += 1

            # MAIZE

            if 20 <= temperature <= 35:
                scores["Maize"] += 2

            if humidity >= 50:
                scores["Maize"] += 1

            if 50 <= rainfall <= 200:
                scores["Maize"] += 2

            if 5.5 <= ph <= 7.5:
                scores["Maize"] += 1

            if nitrogen >= 50:
                scores["Maize"] += 2

            if phosphorus >= 30:
                scores["Maize"] += 1

            if potassium >= 20:
                scores["Maize"] += 1

            # COTTON

            if 25 <= temperature <= 35:
                scores["Cotton"] += 2

            if humidity >= 40:
                scores["Cotton"] += 1

            if 50 <= rainfall <= 150:
                scores["Cotton"] += 2

            if 5.5 <= ph <= 8:
                scores["Cotton"] += 1

            if nitrogen >= 40:
                scores["Cotton"] += 1

            if phosphorus >= 20:
                scores["Cotton"] += 1

            if potassium >= 30:
                scores["Cotton"] += 2

            # SUGARCANE

            if 25 <= temperature <= 35:
                scores["Sugarcane"] += 2

            if humidity >= 60:
                scores["Sugarcane"] += 2

            if rainfall >= 100:
                scores["Sugarcane"] += 2

            if 6 <= ph <= 7.5:
                scores["Sugarcane"] += 1

            if nitrogen >= 80:
                scores["Sugarcane"] += 1

            if phosphorus >= 30:
                scores["Sugarcane"] += 1

            if potassium >= 40:
                scores["Sugarcane"] += 1

            # GROUNDNUT

            if 25 <= temperature <= 35:
                scores["Groundnut"] += 2

            if 40 <= humidity <= 70:
                scores["Groundnut"] += 1

            if 50 <= rainfall <= 100:
                scores["Groundnut"] += 2

            if 5.5 <= ph <= 7:
                scores["Groundnut"] += 2

            if nitrogen <= 60:
                scores["Groundnut"] += 1

            if phosphorus >= 20:
                scores["Groundnut"] += 1

            if potassium >= 20:
                scores["Groundnut"] += 1

            # MILLET

            if 20 <= temperature <= 35:
                scores["Millet"] += 2

            if humidity <= 70:
                scores["Millet"] += 1

            if 30 <= rainfall <= 100:
                scores["Millet"] += 2

            if 5 <= ph <= 7.5:
                scores["Millet"] += 1

            if nitrogen <= 60:
                scores["Millet"] += 1

            if phosphorus <= 50:
                scores["Millet"] += 1

            if potassium <= 50:
                scores["Millet"] += 1

            crop = max(scores, key=scores.get)

        except ValueError:

            crop = "Please enter valid numeric values."

    return render_template(
        "crop_recommendation.html",
        crop=crop
    )


# ==========================================================
# MODULE 2 - WEATHER BASED FARMING ADVISORY
# ==========================================================

@app.route("/weather-advisory", methods=["GET", "POST"])
def weather_advisory():

    advice = None
    alert = None

    if request.method == "POST":

        try:

            temperature = float(request.form["temperature"])
            humidity = float(request.form["humidity"])
            rainfall = float(request.form["rainfall"])

            if humidity < 0 or humidity > 100:

                alert = "Humidity must be between 0 and 100."

            elif rainfall < 0:

                alert = "Rainfall cannot be negative."

            else:

                recommendations = []

                if temperature >= 35:

                    recommendations.append(
                        "High temperature detected. "
                        "Provide sufficient irrigation to prevent crop stress."
                    )

                elif temperature <= 15:

                    recommendations.append(
                        "Low temperature detected. "
                        "Protect sensitive crops from cold conditions."
                    )

                else:

                    recommendations.append(
                        "Temperature is suitable for normal crop growth."
                    )

                if humidity >= 80:

                    recommendations.append(
                        "High humidity detected. "
                        "Monitor crops for fungal diseases and improve air circulation."
                    )

                elif humidity <= 40:

                    recommendations.append(
                        "Low humidity detected. "
                        "Crops may require additional irrigation."
                    )

                else:

                    recommendations.append(
                        "Humidity level is suitable for most crops."
                    )

                if rainfall >= 100:

                    recommendations.append(
                        "Heavy rainfall detected. "
                        "Ensure proper drainage and avoid unnecessary irrigation."
                    )

                elif rainfall <= 20:

                    recommendations.append(
                        "Low rainfall detected. "
                        "Consider irrigation based on soil moisture."
                    )

                else:

                    recommendations.append(
                        "Rainfall level is moderate."
                    )

                advice = recommendations

        except ValueError:

            alert = "Please enter valid numeric values."

    return render_template(
        "weather_advisory.html",
        advice=advice,
        alert=alert
    )


# ==========================================================
# MODULE 3 - IRRIGATION RECOMMENDATION
# ==========================================================

@app.route("/irrigation", methods=["GET", "POST"])
def irrigation():

    recommendation = None
    message = None
    alert = None

    if request.method == "POST":

        try:

            soil_moisture = float(request.form["soil_moisture"])
            temperature = float(request.form["temperature"])
            humidity = float(request.form["humidity"])
            rainfall = float(request.form["rainfall"])

            # ==============================
            # INPUT VALIDATION
            # ==============================

            if soil_moisture < 0 or soil_moisture > 100:

                alert = "Soil moisture must be between 0 and 100."

            elif humidity < 0 or humidity > 100:

                alert = "Humidity must be between 0 and 100."

            elif rainfall < 0:

                alert = "Rainfall cannot be negative."

            else:

                # ==============================
                # IRRIGATION DECISION
                # ==============================

                if rainfall >= 100:

                    recommendation = "No Irrigation Required"

                    message = (
                        "Heavy rainfall has been detected. "
                        "Avoid irrigation and ensure proper drainage "
                        "to prevent waterlogging."
                    )

                elif soil_moisture < 30:

                    recommendation = "Irrigation Required"

                    message = (
                        "Soil moisture is low. "
                        "Irrigate the crop adequately to maintain "
                        "healthy plant growth."
                    )

                elif soil_moisture < 60:

                    recommendation = "Moderate Irrigation"

                    message = (
                        "Soil moisture is at a moderate level. "
                        "Provide irrigation according to the crop's "
                        "water requirement."
                    )

                else:

                    recommendation = "No Irrigation Required"

                    message = (
                        "Soil moisture is sufficient. "
                        "Additional irrigation is not required at this time."
                    )

                # ==============================
                # TEMPERATURE ADVICE
                # ==============================

                if temperature >= 35:

                    message += (
                        " High temperature is also present, so monitor "
                        "the crop for signs of water stress."
                    )

                elif temperature <= 15:

                    message += (
                        " Since the temperature is low, avoid excessive "
                        "irrigation."
                    )

                # ==============================
                # HUMIDITY ADVICE
                # ==============================

                if humidity >= 80:

                    message += (
                        " High humidity is present, so avoid overwatering "
                        "and monitor for fungal diseases."
                    )

        except ValueError:

            alert = "Please enter valid numeric values."

    return render_template(
        "irrigation.html",
        recommendation=recommendation,
        message=message,
        alert=alert
    )


# ==============================
# LOGOUT
# ==============================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("index"))


# ==============================
# RUN APPLICATION
# ==============================

if __name__ == "__main__":
    app.run(debug=True)
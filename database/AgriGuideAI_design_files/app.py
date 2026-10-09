
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename

import os
import numpy as np
import tensorflow as tf
from PIL import Image
from tensorflow.keras.applications.efficientnet import preprocess_input


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)
app.secret_key = "agriguide_secret_key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///farmers.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ============================================================
# DATABASE MODELS
# ============================================================

class Farmer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class CropHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, nullable=False)

    nitrogen = db.Column(db.Float, nullable=False)
    phosphorus = db.Column(db.Float, nullable=False)
    potassium = db.Column(db.Float, nullable=False)

    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    ph = db.Column(db.Float, nullable=False)
    rainfall = db.Column(db.Float, nullable=False)

    crop = db.Column(db.String(100), nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )


class ActivityHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, nullable=False)
    activity_type = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )


with app.app_context():
    db.create_all()


# ============================================================
# SAVE ACTIVITY TO HISTORY
# ============================================================

def save_activity(activity_type, details):
    farmer_id = session.get("farmer_id")

    if farmer_id is None:
        return

    record = ActivityHistory(
        farmer_id=farmer_id,
        activity_type=activity_type,
        details=details
    )

    db.session.add(record)
    db.session.commit()


# ============================================================
# LOAD PLANT DISEASE MODEL
# ============================================================

MODEL_PATH = os.path.join(
    "model",
    "plant_disease_efficientnet.keras"
)

CLASS_NAMES_PATH = os.path.join(
    "model",
    "class_names.txt"
)

plant_model = None
class_names = {}

try:
    print("Loading Plant Disease AI model...")
    plant_model = tf.keras.models.load_model(MODEL_PATH)
    print("Plant Disease AI model loaded successfully!")

except Exception as e:
    print("ERROR loading Plant Disease model:")
    print(e)


try:
    with open(CLASS_NAMES_PATH, "r") as file:
        for line in file:
            line = line.strip()

            if ":" in line:
                index, name = line.split(":", 1)
                class_names[int(index.strip())] = name.strip()

    print("Plant disease classes loaded:", len(class_names))

except Exception as e:
    print("ERROR loading class names:")
    print(e)


# ============================================================
# INDEX AND HOME
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/home")
def home():
    return render_template("home.html")


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template(
                "register.html",
                error="Please complete all fields."
            )

        existing_farmer = Farmer.query.filter_by(
            email=email
        ).first()

        if existing_farmer:
            return render_template(
                "register.html",
                error="Email already registered."
            )

        farmer = Farmer(
            name=name,
            email=email,
            password=password
        )

        db.session.add(farmer)
        db.session.commit()

        return redirect(url_for("success"))

    return render_template("register.html")


@app.route("/success")
def success():
    return render_template("success.html")


# ============================================================
# LOGIN AND DASHBOARD
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        farmer = Farmer.query.filter_by(
            email=email,
            password=password
        ).first()

        if farmer:
            session["farmer_id"] = farmer.id
            session["farmer_name"] = farmer.name

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "farmer_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session.get("farmer_name")
    )


# ============================================================
# CROP RECOMMENDATION
# ============================================================

@app.route("/crop-recommendation", methods=["GET", "POST"])
def crop_recommendation():
    if request.method == "POST":
        try:
            nitrogen = float(request.form.get("nitrogen", 0))
            phosphorus = float(request.form.get("phosphorus", 0))
            potassium = float(request.form.get("potassium", 0))
            temperature = float(request.form.get("temperature", 0))
            humidity = float(request.form.get("humidity", 0))
            ph = float(request.form.get("ph", 0))
            rainfall = float(request.form.get("rainfall", 0))

        except (ValueError, TypeError):
            return render_template(
                "crop_recommendation.html",
                crop="Please enter valid numeric values."
            )

        if rainfall > 150 and humidity > 70:
            crop = "Rice"
        elif temperature > 28 and rainfall < 100:
            crop = "Millet"
        elif phosphorus > nitrogen:
            crop = "Wheat"
        else:
            crop = "Rice"

        farmer_id = session.get("farmer_id")

        if farmer_id is not None:
            record = CropHistory(
                farmer_id=farmer_id,
                nitrogen=nitrogen,
                phosphorus=phosphorus,
                potassium=potassium,
                temperature=temperature,
                humidity=humidity,
                ph=ph,
                rainfall=rainfall,
                crop=crop
            )

            db.session.add(record)
            db.session.commit()

        return render_template(
            "crop_recommendation.html",
            crop=crop
        )

    return render_template("crop_recommendation.html")


# ============================================================
# WEATHER ADVISORY
# ============================================================

@app.route("/weather-advisory", methods=["GET", "POST"])
def weather_advisory():
    advice = []
    alert = None

    if request.method == "POST":
        try:
            temperature = float(request.form.get("temperature", ""))
            humidity = float(request.form.get("humidity", ""))
            rainfall = float(request.form.get("rainfall", ""))

            if not 0 <= humidity <= 100:
                raise ValueError("Humidity must be between 0 and 100.")

            if rainfall < 0:
                raise ValueError("Rainfall cannot be negative.")

            # Generate weather-based farming advice
            if temperature >= 35:
                advice.append(
                    "High temperature detected. Avoid heavy field work "
                    "during the hottest hours and monitor crops for heat stress."
                )
            elif temperature <= 15:
                advice.append(
                    "Cool conditions detected. Monitor crops for "
                    "temperature-related stress."
                )
            else:
                advice.append(
                    "Temperature is within a moderate range. "
                    "Continue regular crop monitoring."
                )

            if humidity >= 80:
                advice.append(
                    "Humidity is high. Inspect crops for fungal diseases "
                    "and avoid unnecessary overhead irrigation."
                )
            elif humidity <= 35:
                advice.append(
                    "Humidity is low. Check soil moisture regularly "
                    "and monitor crops for water stress."
                )
            else:
                advice.append(
                    "Humidity is moderate. Continue monitoring crop health."
                )

            if rainfall >= 50:
                advice.append(
                    "Rainfall is high. Check field drainage and avoid "
                    "irrigating waterlogged fields."
                )
            elif rainfall > 0:
                advice.append(
                    "Rain has been reported. Check soil moisture before "
                    "deciding whether additional irrigation is needed."
                )
            else:
                advice.append(
                    "No rainfall has been reported in the entered data. "
                    "Check soil moisture before watering crops."
                )

            save_activity(
                "Weather Advisory",
                f"Temperature: {temperature} °C, "
                f"Humidity: {humidity}%, Rainfall: {rainfall} mm. "
                f"Advice: {' '.join(advice)}"
            )

        except (ValueError, TypeError):
            alert = (
                "Please enter valid values. Humidity must be from "
                "0 to 100, and rainfall cannot be negative."
            )

    return render_template(
        "weather_advisory.html",
        advice=advice,
        alert=alert
    )


# ============================================================
# FARMING ADVISORY
# ============================================================

@app.route("/farming-advisory", methods=["GET", "POST"])
def farming_advisory():
    advisory = []
    error = None
    selected_crop = None
    selected_problem = None

    if request.method == "POST":
        selected_crop = request.form.get("crop", "").strip()
        selected_problem = request.form.get("problem", "").strip()

        allowed_crops = [
            "Rice", "Wheat", "Maize", "Cotton",
            "Sugarcane", "Groundnut", "Millet"
        ]

        allowed_problems = [
            "Fertilizer Management", "Pest Management",
            "Disease Prevention", "Water Management",
            "Soil Management"
        ]

        if selected_crop not in allowed_crops:
            error = "Please select a valid crop."
        elif selected_problem not in allowed_problems:
            error = "Please select a valid farming problem."
        else:
            # Crop-specific context
            advisory.append(
                f"For {selected_crop}, inspect the crop regularly "
                "and follow recommendations suitable for its growth stage."
            )

            if selected_problem == "Fertilizer Management":
                advisory.extend([
                    "Use a soil test to determine nutrient requirements.",
                    "Apply fertilizer at the recommended rate and growth stage.",
                    "Avoid excessive fertilizer application, which can harm "
                    "plants and contribute to water pollution."
                ])

            elif selected_problem == "Pest Management":
                advisory.extend([
                    "Inspect leaves, stems, and fruits for pest damage.",
                    "Use integrated pest management methods, including "
                    "field sanitation and beneficial insects where appropriate.",
                    "Use only locally approved pesticides and follow the "
                    "product label and recommended safety precautions."
                ])

            elif selected_problem == "Disease Prevention":
                advisory.extend([
                    "Inspect plants regularly for unusual spots, wilting, "
                    "discoloration, or rotting.",
                    "Remove severely affected plant material where appropriate "
                    "and clean tools between affected areas.",
                    "Avoid excessive leaf wetness and seek local agricultural "
                    "guidance if the disease continues to spread."
                ])

            elif selected_problem == "Water Management":
                advisory.extend([
                    "Check soil moisture before irrigation.",
                    "Provide water according to crop growth stage, soil type, "
                    "and local weather conditions.",
                    "Ensure proper drainage and avoid prolonged waterlogging."
                ])

            elif selected_problem == "Soil Management":
                advisory.extend([
                    "Test soil pH and nutrient levels periodically.",
                    "Maintain soil organic matter with suitable compost "
                    "or other locally recommended organic materials.",
                    "Use crop rotation and erosion-control practices "
                    "appropriate to your field."
                ])

            save_activity(
                "Farming Advisory",
                f"Crop: {selected_crop}. "
                f"Problem: {selected_problem}. "
                f"Advice: {' '.join(advisory)}"
            )

    return render_template(
        "farming_advisory.html",
        advisory=advisory,
        error=error,
        selected_crop=selected_crop,
        selected_problem=selected_problem
    )


# ============================================================
# IRRIGATION GUIDANCE
# ============================================================

@app.route("/irrigation", methods=["GET", "POST"])
def irrigation():
    recommendation = None
    message = None
    alert = None

    if request.method == "POST":
        try:
            soil_moisture = float(
                request.form.get("soil_moisture", "")
            )
            temperature = float(
                request.form.get("temperature", "")
            )
            humidity = float(
                request.form.get("humidity", "")
            )
            rainfall = float(
                request.form.get("rainfall", "")
            )

            if not 0 <= soil_moisture <= 100:
                raise ValueError(
                    "Soil moisture must be between 0 and 100."
                )

            if not 0 <= humidity <= 100:
                raise ValueError(
                    "Humidity must be between 0 and 100."
                )

            if rainfall < 0:
                raise ValueError("Rainfall cannot be negative.")

            # Rule-based irrigation guidance
            if soil_moisture < 20 and rainfall < 5:
                recommendation = "Irrigation Recommended"
                message = (
                    "Soil moisture is low and little rainfall is reported. "
                    "Check the root-zone soil and irrigate as appropriate "
                    "for your crop and soil type."
                )

            elif soil_moisture < 35 and temperature >= 30:
                recommendation = "Check Irrigation Requirement"
                message = (
                    "Soil moisture is relatively low and temperature is high. "
                    "Inspect the crop for water stress and consider irrigation "
                    "if the root zone is dry."
                )

            elif soil_moisture >= 60 or rainfall >= 25:
                recommendation = "Irrigation May Not Be Needed Now"
                message = (
                    "The entered soil moisture or rainfall is relatively high. "
                    "Check the soil before adding water and ensure the field "
                    "has adequate drainage."
                )

            else:
                recommendation = "Monitor Soil Moisture"
                message = (
                    "Check soil moisture and crop condition again before "
                    "irrigating. Actual water needs depend on crop type, "
                    "growth stage, soil, and local conditions."
                )

            save_activity(
                "Irrigation Guidance",
                f"Soil moisture: {soil_moisture}%, "
                f"Temperature: {temperature} °C, "
                f"Humidity: {humidity}%, Rainfall: {rainfall} mm. "
                f"Result: {recommendation}. {message}"
            )

        except (ValueError, TypeError):
            alert = (
                "Please enter valid numbers. Soil moisture and humidity "
                "must be from 0 to 100, and rainfall cannot be negative."
            )

    return render_template(
        "irrigation.html",
        recommendation=recommendation,
        message=message,
        alert=alert
    )


# ============================================================
# PLANT DISEASE DETECTION
# ============================================================

@app.route("/plant-disease", methods=["GET", "POST"])
def plant_disease():
    result = None
    confidence = None
    error = None

    if request.method == "GET":
        return render_template(
            "plant_disease.html",
            result=result,
            confidence=confidence,
            error=error
        )

    if plant_model is None:
        error = "Plant Disease AI model could not be loaded."

        return render_template(
            "plant_disease.html",
            result=result,
            confidence=confidence,
            error=error
        )

    if "plant_image" not in request.files:
        error = "Please select a leaf image."

        return render_template(
            "plant_disease.html",
            result=result,
            confidence=confidence,
            error=error
        )

    file = request.files["plant_image"]

    if file.filename == "":
        error = "Please select a leaf image."

        return render_template(
            "plant_disease.html",
            result=result,
            confidence=confidence,
            error=error
        )

    try:
        filename = secure_filename(file.filename)

        img = Image.open(file).convert("RGB")
        img = img.resize((224, 224))

        x = np.array(img)
        x = np.array([x])
        x = preprocess_input(x)

        predictions = plant_model.predict(x, verbose=0)[0]

        predicted_index = int(np.argmax(predictions))
        confidence = float(predictions[predicted_index] * 100)

        result = class_names.get(
            predicted_index,
            f"Class {predicted_index}"
        )

        save_activity(
            "Plant Disease Detection",
            f"Image: {filename or 'Uploaded image'}. "
            f"Detected result: {result}. "
            f"Confidence: {confidence:.2f}%."
        )

    except Exception as e:
        print("ERROR during plant disease detection:")
        print(e)

        error = (
            "Unable to process the image. "
            "Please upload a valid leaf image."
        )

    return render_template(
        "plant_disease.html",
        result=result,
        confidence=confidence,
        error=error
    )


# ============================================================
# MY HISTORY
# ============================================================

@app.route("/my-history")
def my_history():
    if "farmer_id" not in session:
        return redirect(url_for("login"))

    farmer_id = session["farmer_id"]

    crop_records = CropHistory.query.filter_by(
        farmer_id=farmer_id
    ).order_by(
        CropHistory.created_at.desc()
    ).all()

    activity_records = ActivityHistory.query.filter_by(
        farmer_id=farmer_id
    ).order_by(
        ActivityHistory.created_at.desc()
    ).all()

    all_history = []

    for item in crop_records:
        all_history.append({
            "created_at": item.created_at,
            "activity_type": "Crop Recommendation",
            "details": (
                f"Recommended crop: {item.crop}. "
                f"N: {item.nitrogen}, P: {item.phosphorus}, "
                f"K: {item.potassium}, Temperature: {item.temperature}, "
                f"Humidity: {item.humidity}, pH: {item.ph}, "
                f"Rainfall: {item.rainfall}"
            )
        })

    for item in activity_records:
        all_history.append({
            "created_at": item.created_at,
            "activity_type": item.activity_type,
            "details": item.details
        })

    all_history.sort(
        key=lambda record: record["created_at"],
        reverse=True
    )

    return render_template(
        "history.html",
        history=all_history,
        name=session.get("farmer_name")
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    print("AgriGuideAI Application Starting")
    print("Open: http://127.0.0.1:5000")

    app.run(debug=True)



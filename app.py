
import os
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "agriguide_secret_key"
)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + os.path.join(BASE_DIR, "instance", "farmers.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

db = SQLAlchemy(app)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR, "static", "uploads"
)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


# --------------------------------------------------
# MACHINE LEARNING MODEL
# --------------------------------------------------

disease_model = None
class_names = []

MODEL_PATH = os.path.join(
    BASE_DIR, "model", "plant_disease_efficientnet.keras"
)
CLASS_NAMES_PATH = os.path.join(
    BASE_DIR, "model", "class_names.txt"
)

try:
    from tensorflow.keras.models import load_model

    if os.path.exists(MODEL_PATH):
        disease_model = load_model(MODEL_PATH)
        app.logger.info("Plant disease model loaded successfully.")
    else:
        app.logger.warning("Plant disease model file was not found.")

    if os.path.exists(CLASS_NAMES_PATH):
        with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as file:
            class_names = [
                line.strip()
                for line in file
                if line.strip()
            ]

except Exception:
    app.logger.exception("Could not load the plant disease model.")


# --------------------------------------------------
# DATABASE MODELS
# These columns match the existing database schema.
# Do not delete your existing farmers.db file.
# --------------------------------------------------

class Farmer(db.Model):
    __tablename__ = "farmer"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(
        db.String(150), unique=True, nullable=False
    )
    password = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(200))


class CropHistory(db.Model):
    __tablename__ = "crop_history"

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(
        db.Integer, db.ForeignKey("farmer.id"), nullable=False
    )
    nitrogen = db.Column(db.Float)
    phosphorus = db.Column(db.Float)
    potassium = db.Column(db.Float)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    ph = db.Column(db.Float)
    rainfall = db.Column(db.Float)
    crop = db.Column(db.String(100))
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow
    )


class ActivityHistory(db.Model):
    __tablename__ = "activity_history"

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(
        db.Integer, db.ForeignKey("farmer.id"), nullable=False
    )
    activity_type = db.Column(db.String(100))
    details = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow
    )

    @property
    def activity(self):
        return self.activity_type


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def login_required():
    return "farmer_id" in session


def login_guard():
    if not login_required():
        flash("Please log in to continue.", "error")
        return redirect(url_for("login"))
    return None


def record_activity(activity_type, details):
    farmer_id = session.get("farmer_id")

    if farmer_id is None:
        return

    try:
        activity = ActivityHistory(
            farmer_id=farmer_id,
            activity_type=activity_type,
            details=details,
        )
        db.session.add(activity)
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Could not save activity history.")


def render_existing_template(template_names, **context):
    for template_name in template_names:
        try:
            app.jinja_env.get_template(template_name)
            return render_template(template_name, **context)
        except Exception:
            continue

    app.logger.error(
        "None of these templates exists: %s", template_names
    )
    return (
        "Required HTML template not found. Check the templates folder.",
        500,
    )


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def recommend_crop(nitrogen, phosphorus, potassium,
                   temperature, humidity, ph, rainfall):
    # Basic fallback recommendation using the submitted values.
    # Replace this function with your trained crop model if available.

    if humidity >= 80 and rainfall >= 150:
        return "Rice"
    elif temperature < 20 and rainfall < 100:
        return "Chickpea"
    elif temperature >= 25 and humidity < 60:
        return "Millet"
    elif nitrogen >= 80 and rainfall >= 80:
        return "Maize"
    elif 5.5 <= ph <= 7.5 and rainfall >= 50:
        return "Wheat"
    else:
        return "Millet"


def create_farming_advice(crop, soil_type, season):
    crop = crop.strip().lower()
    soil_type = soil_type.strip().lower()
    season = season.strip().lower()

    advice = [
        "Check soil moisture regularly before watering.",
        "Use healthy, certified seeds suitable for your region.",
        "Monitor crops for pests and disease symptoms.",
        "Apply fertilizers according to soil-test results.",
    ]

    if "rice" in crop or "paddy" in crop:
        advice.append(
            "Manage field water carefully and avoid unnecessary "
            "continuous flooding where alternate practices are suitable."
        )
    elif "millet" in crop:
        advice.append(
            "Avoid overwatering and monitor the crop during dry periods."
        )
    elif "wheat" in crop:
        advice.append(
            "Monitor soil moisture during germination and grain development."
        )

    if "sandy" in soil_type:
        advice.append(
            "Sandy soil drains quickly; use smaller, appropriately "
            "timed irrigation applications."
        )
    elif "clay" in soil_type:
        advice.append(
            "Clay soil holds water longer; avoid waterlogging."
        )

    if "summer" in season:
        advice.append(
            "Water during cooler parts of the day when practical."
        )
    elif "rainy" in season or "monsoon" in season:
        advice.append(
            "Ensure field drainage and monitor fungal disease risks."
        )

    return advice


def predict_plant_disease(image_path):
    if disease_model is None:
        raise RuntimeError(
            "Plant disease model is unavailable. "
            "Check the model file and TensorFlow installation."
        )

    from PIL import Image
    import numpy as np

    image = Image.open(image_path).convert("RGB")

    input_shape = disease_model.input_shape
    if isinstance(input_shape, list):
        input_shape = input_shape[0]

    height = input_shape[1] or 224
    width = input_shape[2] or 224

    image = image.resize((width, height))
    image_array = np.asarray(image, dtype=np.float32) / 255.0
    image_array = np.expand_dims(image_array, axis=0)

    predictions = disease_model.predict(
        image_array, verbose=0
    )
    probabilities = predictions[0]

    predicted_index = int(np.argmax(probabilities))
    confidence = float(probabilities[predicted_index]) * 100

    if predicted_index < len(class_names):
        label = class_names[predicted_index]
    else:
        label = f"Class {predicted_index}"

    return label, round(confidence, 2)


# --------------------------------------------------
# HOME AND LOGIN
# --------------------------------------------------

@app.route("/")
def index():
    if login_required():
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash(
                "Please enter both email and password.",
                "error",
            )
            return render_template("login.html")

        try:
            farmer = Farmer.query.filter_by(
                email=email
            ).first()

            # This comparison matches the original plain-text
            # password format. Hashed passwords need verification
            # with the matching password-hashing function.
            if farmer and farmer.password == password:
                session.clear()
                session["farmer_id"] = farmer.id
                session["farmer_name"] = farmer.name

                return redirect(url_for("home"))

            flash("Invalid email or password.", "error")

        except Exception:
            db.session.rollback()
            app.logger.exception("Login failed.")
            flash(
                "A login error occurred. Please try again.",
                "error",
            )

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        location = request.form.get("location", "").strip()

        if not name or not email or not password:
            flash(
                "Please complete all required fields.",
                "error",
            )
            return render_template("register.html")

        try:
            existing_farmer = Farmer.query.filter_by(
                email=email
            ).first()

            if existing_farmer:
                flash(
                    "This email is already registered. Please log in.",
                    "error",
                )
                return render_template("register.html")

            farmer = Farmer(
                name=name,
                email=email,
                password=password,
                location=location,
            )

            db.session.add(farmer)
            db.session.commit()

            flash(
                "Registration successful. Please log in.",
                "success",
            )
            return redirect(url_for("login"))

        except Exception:
            db.session.rollback()
            app.logger.exception("Registration failed.")
            flash(
                "Registration failed. Please try again.",
                "error",
            )

    return render_template("register.html")


@app.route("/home")
def home():
    response = login_guard()
    if response:
        return response

    return render_existing_template(
        ["home.html", "dashboard.html"],
        farmer_name=session.get("farmer_name", "Farmer"),
    )


@app.route("/dashboard")
def dashboard():
    response = login_guard()
    if response:
        return response

    return render_existing_template(
        ["dashboard.html", "home.html"],
        farmer_name=session.get("farmer_name", "Farmer"),
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# --------------------------------------------------
# CROP RECOMMENDATION
# --------------------------------------------------

@app.route("/crop-recommendation", methods=["GET", "POST"])
def crop_recommendation():
    response = login_guard()
    if response:
        return response

    recommendation = None
    result = None
    values = {}

    if request.method == "POST":
        field_names = [
            "nitrogen",
            "phosphorus",
            "potassium",
            "temperature",
            "humidity",
            "ph",
            "rainfall",
        ]

        try:
            for field in field_names:
                values[field] = float(
                    request.form.get(field, "")
                )

            recommendation = recommend_crop(
                values["nitrogen"],
                values["phosphorus"],
                values["potassium"],
                values["temperature"],
                values["humidity"],
                values["ph"],
                values["rainfall"],
            )
            result = recommendation

            history = CropHistory(
                farmer_id=session["farmer_id"],
                nitrogen=values["nitrogen"],
                phosphorus=values["phosphorus"],
                potassium=values["potassium"],
                temperature=values["temperature"],
                humidity=values["humidity"],
                ph=values["ph"],
                rainfall=values["rainfall"],
                crop=recommendation,
            )
            db.session.add(history)
            db.session.commit()

            record_activity(
                "Crop Recommendation",
                f"Recommended crop: {recommendation}",
            )

        except (ValueError, TypeError):
            db.session.rollback()
            flash(
                "Enter valid numeric values in all crop fields.",
                "error",
            )
        except Exception:
            db.session.rollback()
            app.logger.exception(
                "Crop recommendation failed."
            )
            flash(
                "Could not generate a crop recommendation.",
                "error",
            )

    return render_existing_template(
        ["crop_recommendation.html"],
        recommendation=recommendation,
        result=result,
        values=values,
    )


# --------------------------------------------------
# FARMING ADVISORY
# --------------------------------------------------

@app.route("/farming-advisory", methods=["GET", "POST"])
def farming_advisory():
    response = login_guard()
    if response:
        return response

    advice = []
    recommendations = []

    if request.method == "POST":
        crop = request.form.get("crop", "").strip()
        soil_type = request.form.get("soil_type", "").strip()
        season = request.form.get("season", "").strip()

        if not crop or not soil_type or not season:
            flash(
                "Enter the crop, soil type, and season.",
                "error",
            )
        else:
            advice = create_farming_advice(
                crop, soil_type, season
            )
            recommendations = advice

            record_activity(
                "Farming Advisory",
                f"Crop: {crop}; Soil: {soil_type}; Season: {season}",
            )

    return render_existing_template(
        ["farming_advisory.html"],
        advice=advice,
        recommendations=recommendations,
    )


# --------------------------------------------------
# WEATHER ADVISORY
# --------------------------------------------------

@app.route("/weather-advisory", methods=["GET", "POST"])
def weather_advisory():
    response = login_guard()
    if response:
        return response

    advice = []
    weather = None

    if request.method == "POST":
        temperature_text = request.form.get(
            "temperature", ""
        ).strip()
        humidity_text = request.form.get(
            "humidity", ""
        ).strip()
        rainfall_text = request.form.get(
            "rainfall", ""
        ).strip()

        try:
            temperature = float(temperature_text)
            humidity = float(humidity_text)
            rainfall = float(rainfall_text)

            weather = {
                "temperature": temperature,
                "humidity": humidity,
                "rainfall": rainfall,
            }

            if temperature >= 35:
                advice.append(
                    "High temperature: monitor soil moisture "
                    "and avoid water stress."
                )
            elif temperature <= 15:
                advice.append(
                    "Cool conditions: monitor crops for "
                    "temperature-related stress."
                )
            else:
                advice.append(
                    "Temperature is within a moderate range "
                    "for many crops; consider crop-specific needs."
                )

            if humidity >= 80:
                advice.append(
                    "High humidity can increase some fungal "
                    "disease risks. Inspect crops regularly."
                )
            elif humidity <= 35:
                advice.append(
                    "Low humidity may increase moisture loss. "
                    "Check soil moisture."
                )

            if rainfall >= 100:
                advice.append(
                    "High rainfall: check drainage and prevent "
                    "waterlogging."
                )
            elif rainfall <= 10:
                advice.append(
                    "Low rainfall: assess irrigation needs "
                    "before watering."
                )

            if not advice:
                advice.append(
                    "Monitor local forecasts and soil conditions."
                )

            record_activity(
                "Weather Advisory",
                (
                    f"Temperature: {temperature}; "
                    f"Humidity: {humidity}; Rainfall: {rainfall}"
                ),
            )

        except (ValueError, TypeError):
            flash(
                "Enter valid temperature, humidity, and rainfall values.",
                "error",
            )

    return render_existing_template(
        ["weather_advisory.html", "farming_advisory.html"],
        advice=advice,
        recommendations=advice,
        weather=weather,
    )


# --------------------------------------------------
# IRRIGATION GUIDANCE
# --------------------------------------------------

@app.route("/irrigation", methods=["GET", "POST"])
def irrigation():
    response = login_guard()
    if response:
        return response

    recommendation = None
    result = None

    if request.method == "POST":
        crop = request.form.get("crop", "").strip()
        soil_type = request.form.get("soil_type", "").strip()
        moisture_text = request.form.get(
            "soil_moisture", ""
        ).strip()

        try:
            moisture = float(moisture_text)

            if moisture < 0 or moisture > 100:
                raise ValueError(
                    "Soil moisture must be between 0 and 100."
                )

            if moisture < 30:
                recommendation = (
                    "Soil moisture is low. Check the crop's "
                    "water requirements and consider irrigation."
                )
            elif moisture < 60:
                recommendation = (
                    "Soil moisture is moderate. Check the crop "
                    "and soil before deciding to irrigate."
                )
            else:
                recommendation = (
                    "Soil moisture is relatively high. Check "
                    "drainage and avoid unnecessary watering."
                )

            result = recommendation

            record_activity(
                "Irrigation Guidance",
                (
                    f"Crop: {crop}; Soil: {soil_type}; "
                    f"Moisture: {moisture}%"
                ),
            )

        except (ValueError, TypeError):
            flash(
                "Enter a valid soil moisture value from 0 to 100.",
                "error",
            )

    return render_existing_template(
        ["irrigation.html"],
        recommendation=recommendation,
        result=result,
    )


# --------------------------------------------------
# PLANT DISEASE DETECTOR
# --------------------------------------------------

@app.route("/plant-disease", methods=["GET", "POST"])
def plant_disease():
    response = login_guard()
    if response:
        return response

    prediction = None
    confidence = None
    image_url = None

    if request.method == "POST":
        if "image" not in request.files:
            flash("Please select a plant image.", "error")
            return redirect(url_for("plant_disease"))

        uploaded_file = request.files["image"]

        if not uploaded_file or not uploaded_file.filename:
            flash("Please select a plant image.", "error")
            return redirect(url_for("plant_disease"))

        if not allowed_file(uploaded_file.filename):
            flash(
                "Upload a JPG, JPEG, PNG, or WEBP image.",
                "error",
            )
            return redirect(url_for("plant_disease"))

        try:
            timestamp = datetime.now().strftime(
                "%Y%m%d%H%M%S%f"
            )
            safe_name = secure_filename(
                uploaded_file.filename
            )
            filename = (
                f"{session['farmer_id']}_{timestamp}_{safe_name}"
            )

            image_path = os.path.join(
                UPLOAD_FOLDER, filename
            )
            uploaded_file.save(image_path)

            prediction, confidence = predict_plant_disease(
                image_path
            )
            image_url = url_for(
                "static",
                filename=f"uploads/{filename}",
            )

            record_activity(
                "Plant Disease Detection",
                (
                    f"Prediction: {prediction}; "
                    f"Confidence: {confidence}%"
                ),
            )

        except Exception:
            app.logger.exception(
                "Plant disease detection failed."
            )
            flash(
                "Disease detection failed. Check the model "
                "and uploaded image, then try again.",
                "error",
            )

    return render_existing_template(
        [
            "plant_disease.html",
            "plant_disease_detector.html",
            "disease_detection.html",
        ],
        prediction=prediction,
        confidence=confidence,
        image_url=image_url,
    )


# --------------------------------------------------
# MY HISTORY
# --------------------------------------------------

@app.route("/my-history")
def my_history():
    response = login_guard()
    if response:
        return response

    farmer_id = session["farmer_id"]

    try:
        crop_history = (
            CropHistory.query
            .filter_by(farmer_id=farmer_id)
            .order_by(CropHistory.created_at.desc())
            .all()
        )

        activity_history = (
            ActivityHistory.query
            .filter_by(farmer_id=farmer_id)
            .order_by(ActivityHistory.created_at.desc())
            .all()
        )

        return render_template(
            "my_history.html",
            crop_history=crop_history,
            activity_history=activity_history,
            histories=crop_history,
        )

    except Exception:
        db.session.rollback()
        app.logger.exception(
            "My History database query failed."
        )
        flash("Could not load your history.", "error")
        return redirect(url_for("home"))


# --------------------------------------------------
# INITIALIZE DATABASE AND START SERVER
# --------------------------------------------------

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)

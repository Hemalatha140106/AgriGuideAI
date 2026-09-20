from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

import os
import numpy as np
import tensorflow as tf
from PIL import Image
from tensorflow.keras.applications.efficientnet import preprocess_input


# ============================================================
# FLASK APP CONFIGURATION
# ============================================================

app = Flask(__name__)

app.secret_key = "agriguide_secret_key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///farmers.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ============================================================
# FARMER DATABASE MODEL
# ============================================================

class Farmer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


# ============================================================
# CREATE DATABASE
# ============================================================

with app.app_context():
    db.create_all()


# ============================================================
# PLANT DISEASE AI MODEL
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


# ------------------------------------------------------------
# Load AI model
# ------------------------------------------------------------

try:

    print("Loading Plant Disease AI model...")

    plant_model = tf.keras.models.load_model(
        MODEL_PATH
    )

    print("Plant Disease AI model loaded successfully!")

    print("Model input shape:", plant_model.input_shape)
    print("Model output shape:", plant_model.output_shape)

except Exception as e:

    print("ERROR loading Plant Disease model:")
    print(e)


# ------------------------------------------------------------
# Load class names
# ------------------------------------------------------------

try:

    with open(CLASS_NAMES_PATH, "r") as file:

        for line in file:

            line = line.strip()

            if ":" in line:

                index, name = line.split(":", 1)

                class_names[int(index.strip())] = name.strip()

    print(
        "Plant disease classes loaded:",
        len(class_names)
    )

except Exception as e:

    print("ERROR loading class names:")
    print(e)


# ============================================================
# HOME / INDEX
# ============================================================

@app.route("/")
def index():

    return render_template("index.html")


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/home")
def home():

    return render_template("home.html")


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if email already exists
        existing_farmer = Farmer.query.filter_by(
            email=email
        ).first()

        if existing_farmer:

            return render_template(
                "register.html",
                error="Email already registered."
            )

        # Create farmer
        farmer = Farmer(
            name=name,
            email=email,
            password=password
        )

        db.session.add(farmer)
        db.session.commit()

        return redirect(url_for("success"))

    return render_template("register.html")


# ============================================================
# REGISTER SUCCESS
# ============================================================

@app.route("/success")
def success():

    return render_template("success.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

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


# ============================================================
# DASHBOARD
# ============================================================

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

        nitrogen = float(request.form.get("nitrogen", 0))
        phosphorus = float(request.form.get("phosphorus", 0))
        potassium = float(request.form.get("potassium", 0))
        temperature = float(request.form.get("temperature", 0))
        humidity = float(request.form.get("humidity", 0))
        ph = float(request.form.get("ph", 0))
        rainfall = float(request.form.get("rainfall", 0))

        # Simple advisory logic
        if rainfall > 150 and humidity > 70:

            crop = "Rice"

        elif temperature > 28 and rainfall < 100:

            crop = "Millet"

        elif phosphorus > nitrogen:

            crop = "Wheat"

        else:

            crop = "Rice"

        return render_template(
            "crop_recommendation.html",
            crop=crop
        )

    return render_template(
        "crop_recommendation.html"
    )


# ============================================================
# WEATHER ADVISORY
# ============================================================

@app.route("/weather-advisory")
def weather_advisory():

    return render_template(
        "farming_advisory.html"
    )


# ============================================================
# IRRIGATION
# ============================================================

@app.route("/irrigation")
def irrigation():

    return render_template(
        "irrigation.html"
    )


# ============================================================
# FARMING ADVISORY
# ============================================================

@app.route("/farming-advisory")
def farming_advisory():

    return render_template(
        "farming_advisory.html"
    )


# ============================================================
# PLANT DISEASE DETECTION
# ============================================================

@app.route(
    "/plant-disease",
    methods=["GET", "POST"]
)
def plant_disease():

    result = None
    confidence = None
    error = None

    # --------------------------------------------------------
    # GET REQUEST
    # --------------------------------------------------------

    if request.method == "GET":

        return render_template(
            "plant_disease.html",
            result=result,
            confidence=confidence,
            error=error
        )

    # --------------------------------------------------------
    # Check AI model
    # --------------------------------------------------------

    if plant_model is None:

        error = (
            "Plant Disease AI model could not be loaded."
        )

        return render_template(
            "plant_disease.html",
            result=result,
            confidence=confidence,
            error=error
        )

    # --------------------------------------------------------
    # Check uploaded image
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Process image
    # --------------------------------------------------------

    try:

        print("\n========================================")
        print("PLANT DISEASE DETECTION")
        print("========================================")

        print("Uploaded image:", file.filename)

        # Open image
        img = Image.open(file).convert("RGB")

        print("Original image size:", img.size)

        # Resize to model input size
        img = img.resize((224, 224))

        # Convert image to NumPy array
        x = np.array(img)

        print("Image array shape:", x.shape)

        print(
            "Pixel range before preprocessing:",
            x.min(),
            "-",
            x.max()
        )

        # ----------------------------------------------------
        # IMPORTANT
        # Use EfficientNet preprocessing
        # exactly like the model test
        # ----------------------------------------------------

        x = np.array([x])

        x = preprocess_input(x)

        print(
            "Pixel range after preprocessing:",
            x.min(),
            "-",
            x.max()
        )

        print("Final input shape:", x.shape)

        # ----------------------------------------------------
        # AI prediction
        # ----------------------------------------------------

        predictions = plant_model.predict(
            x,
            verbose=0
        )[0]

        # Get predicted class
        predicted_index = int(
            np.argmax(predictions)
        )

        # Get confidence
        confidence = float(
            predictions[predicted_index] * 100
        )

        # Get class name
        result = class_names.get(
            predicted_index,
            f"Class {predicted_index}"
        )

        print(
            "Predicted index:",
            predicted_index
        )

        print(
            "Predicted disease:",
            result
        )

        print(
            "Confidence:",
            f"{confidence:.2f}%"
        )

        # ----------------------------------------------------
        # Show top 5 predictions in terminal
        # ----------------------------------------------------

        top_indices = predictions.argsort()[-5:][::-1]

        print("\nTop 5 predictions:")

        for index in top_indices:

            class_name = class_names.get(
                int(index),
                f"Class {index}"
            )

            probability = predictions[index] * 100

            print(
                f"{class_name}: "
                f"{probability:.2f}%"
            )

        print("========================================\n")

    except Exception as e:

        print("\nERROR during plant disease detection:")
        print(e)

        error = (
            "Unable to process the image. "
            "Please upload a valid leaf image."
        )

    # --------------------------------------------------------
    # Return result to webpage
    # --------------------------------------------------------

    return render_template(
        "plant_disease.html",
        result=result,
        confidence=confidence,
        error=error
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ============================================================
# RUN FLASK APPLICATION
# ============================================================

if __name__ == "__main__":

    print("\n========================================")
    print("AgriGuideAI Application Starting")
    print("========================================")
    print("Open: http://127.0.0.1:5000")
    print("========================================\n")

    app.run(
        debug=True
    )

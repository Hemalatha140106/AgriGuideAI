import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.efficientnet import preprocess_input


MODEL_PATH = "model/plant_disease_efficientnet.keras"
CLASS_NAMES_PATH = "model/class_names.txt"


# ---------------------------------------
# Load model
# ---------------------------------------
print("Loading model...")

model = tf.keras.models.load_model(MODEL_PATH)

print("Model loaded successfully!")
print("Input shape:", model.input_shape)
print("Output shape:", model.output_shape)


# ---------------------------------------
# Load class names
# ---------------------------------------
class_names = {}

with open(CLASS_NAMES_PATH, "r") as file:
    for line in file:
        line = line.strip()

        if ":" in line:
            index, name = line.split(":", 1)
            class_names[int(index.strip())] = name.strip()

print("Number of classes:", len(class_names))


# ---------------------------------------
# Prediction function
# ---------------------------------------
def predict_image(image_path):

    print("\n--------------------------------")
    print("Testing:", image_path)
    print("--------------------------------")

    # Load image exactly like original model code
    img = image.load_img(
        image_path,
        target_size=(224, 224)
    )

    # Convert image to NumPy array
    x = image.img_to_array(img)

    # Add batch dimension
    x = np.array([x])

    print("Input before preprocessing:")
    print("Shape:", x.shape)
    print("Min:", x.min())
    print("Max:", x.max())

    # IMPORTANT:
    # Use the preprocessing method from
    # the original model repository
    x = preprocess_input(x)

    print("Input after EfficientNet preprocessing:")
    print("Min:", x.min())
    print("Max:", x.max())

    # Prediction
    predictions = model.predict(x, verbose=0)[0]

    # Get top 5 predictions
    top_indices = predictions.argsort()[-5:][::-1]

    print("\nTop 5 Predictions:")

    for position, index in enumerate(top_indices, start=1):

        class_name = class_names.get(
            int(index),
            f"Class {index}"
        )

        confidence = predictions[index] * 100

        print(
            f"{position}. "
            f"{class_name} "
            f"= {confidence:.2f}%"
        )

    # Top prediction
    predicted_index = int(np.argmax(predictions))

    predicted_class = class_names.get(
        predicted_index,
        f"Class {predicted_index}"
    )

    confidence = predictions[predicted_index] * 100

    print("\nFINAL RESULT")
    print("--------------------------------")
    print("Predicted index:", predicted_index)
    print("Predicted class:", predicted_class)
    print("Confidence:", f"{confidence:.2f}%")

    return predicted_class, confidence


# ---------------------------------------
# Test images
# ---------------------------------------
files = [
    "model/test1.jpg.jpg",
    "model/test2.jpg.jpg"
]


# ---------------------------------------
# Run tests
# ---------------------------------------
for file in files:

    try:
        predict_image(file)

    except Exception as e:

        print("\nERROR:")
        print(e)


print("\n================================")
print("TEST COMPLETED")
print("================================")
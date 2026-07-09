from __future__ import division, print_function
import os
import uuid

import numpy as np
from flask import Flask, jsonify, render_template, request
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from werkzeug.utils import secure_filename

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "cervical_cancer_image_classifier.h5")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
IMG_SIZE = (256, 256)

# IMPORTANT: this order must match the alphabetical class-index mapping that
# Keras' flow_from_directory() assigns during training (it sorts the class
# subfolder names alphabetically and assigns indices 0, 1, 2... in that
# order). If you retrain on differently-named folders, update this list to
# match the new alphabetical order, not the order you "expect".
CLASS_LABELS = ["Negative", "Positive", "Suspected"]

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload cap

print("Loading model...")
model = load_model(MODEL_PATH)
print("Model loaded. Visit http://127.0.0.1:5000/")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def model_predict(img_path, model):
    img = image.load_img(img_path, target_size=IMG_SIZE)
    x = image.img_to_array(img)
    x = x / 255.0
    x = np.expand_dims(x, axis=0)
    preds = model.predict(x, verbose=0)
    return preds


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file was sent."}), 400

    f = request.files["file"]

    if f.filename == "":
        return jsonify({"error": "No file was selected."}), 400

    if not allowed_file(f.filename):
        return jsonify({"error": "Please upload a PNG or JPG image."}), 400

    filename = f"{uuid.uuid4().hex}_{secure_filename(f.filename)}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    f.save(file_path)

    try:
        preds = model_predict(file_path, model)[0]
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Could not analyze image: {exc}"}), 500
    finally:
        # Uploaded images aren't kept around after inference.
        if os.path.exists(file_path):
            os.remove(file_path)

    probabilities = {label: float(p) for label, p in zip(CLASS_LABELS, preds)}
    top_idx = int(np.argmax(preds))

    return jsonify(
        {
            "label": CLASS_LABELS[top_idx],
            "confidence": float(preds[top_idx]),
            "probabilities": probabilities,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)

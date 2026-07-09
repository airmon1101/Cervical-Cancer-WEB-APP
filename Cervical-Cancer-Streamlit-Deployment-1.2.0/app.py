from __future__ import annotations

import base64
import io
from pathlib import Path

import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from tensorflow.keras.models import load_model

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "cervical_cancer_image_classifier.h5"
FRONTEND_DIR = BASE_DIR / "frontend"
IMG_SIZE = (256, 256)
CLASS_LABELS = ["Positive", "Negative", "Suspected"]

st.set_page_config(
    page_title="Cytoscan — Cervical Cytology Screening Assist",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      #MainMenu, header, footer, [data-testid="stToolbar"],
      [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }
      html, body, [data-testid="stAppViewContainer"], .stApp { margin: 0 !important; padding: 0 !important; }
      [data-testid="stAppViewContainer"] > .main { padding: 0 !important; }
      .block-container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
      [data-testid="stVerticalBlock"] { gap: 0 !important; }
      iframe { display: block; border: 0 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

cytoscan = components.declare_component("cytoscan_frontend", path=str(FRONTEND_DIR))


@st.cache_resource(show_spinner=False)
def get_model():
    return load_model(MODEL_PATH, compile=False)


def decode_data_url(data_url: str) -> Image.Image:
    if not data_url.startswith("data:image/") or "," not in data_url:
        raise ValueError("Invalid image data.")
    encoded = data_url.split(",", 1)[1]
    raw = base64.b64decode(encoded, validate=True)
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError("Image is larger than the 10 MB upload limit.")
    image = Image.open(io.BytesIO(raw))
    return image.convert("RGB")


def predict_image(data_url: str) -> dict:
    image = decode_data_url(data_url).resize(IMG_SIZE)
    x = np.asarray(image, dtype=np.float32) / 255.0
    x = np.expand_dims(x, axis=0)
    preds = np.asarray(get_model().predict(x, verbose=0)[0], dtype=np.float32)

    if preds.shape[0] != len(CLASS_LABELS):
        raise ValueError(f"Model returned {preds.shape[0]} outputs; expected {len(CLASS_LABELS)}.")

    top_idx = int(np.argmax(preds))
    return {
        "label": CLASS_LABELS[top_idx],
        "confidence": float(preds[top_idx]),
        "probabilities": {
            label: float(probability)
            for label, probability in zip(CLASS_LABELS, preds)
        },
    }


if "prediction_payload" not in st.session_state:
    st.session_state.prediction_payload = None
if "last_request_id" not in st.session_state:
    st.session_state.last_request_id = None

component_value = cytoscan(
    prediction=st.session_state.prediction_payload,
    key="cytoscan-ui",
    default=None,
)

if isinstance(component_value, dict) and component_value.get("type") == "analyze":
    request_id = component_value.get("request_id")
    if request_id and request_id != st.session_state.last_request_id:
        st.session_state.last_request_id = request_id
        try:
            result = predict_image(component_value.get("data_url", ""))
            st.session_state.prediction_payload = {
                "request_id": request_id,
                "ok": True,
                "data": result,
            }
        except Exception as exc:
            st.session_state.prediction_payload = {
                "request_id": request_id,
                "ok": False,
                "error": f"Could not analyze image: {exc}",
            }
        st.rerun()

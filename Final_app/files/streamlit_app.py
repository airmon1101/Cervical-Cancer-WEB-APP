import base64
import io
import os

import numpy as np
import streamlit as st
from PIL import Image
from tensorflow.keras.models import load_model

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "cervical_cancer_image_classifier.h5")
IMG_SIZE = (256, 256)

# IMPORTANT: this order must match the alphabetical class-index mapping that
# Keras' flow_from_directory() assigns during training. If you retrain on
# differently-named folders, update this list to match the new alphabetical
# order, not the order you "expect".
CLASS_LABELS = ["Negative", "Positive", "Suspected"]

NOTES = {
    "Negative": "No malignant or pre-malignant features detected in this specimen.",
    "Suspected": "Some atypical features were detected. Manual review is recommended.",
    "Positive": "Features consistent with malignancy were detected. Refer for confirmation.",
}

BAR_COLOR = {
    "Negative": "#6e8f7c",
    "Suspected": "#c98a2c",
    "Positive": "#b24b36",
}

VERDICT_COLOR = BAR_COLOR

st.set_page_config(page_title="Cytoscan", page_icon="🔬", layout="wide")


# ---------------------------------------------------------------------------
# Helper: st.markdown() treats any line indented 4+ spaces as a Markdown code
# block, which silently breaks <style>/<div> injection the moment this code
# lives inside an indented `with`/`if`/`for` block in Python (the deeper the
# nesting, the more leading spaces the string literally contains). Stripping
# each line individually — not just the common indent via textwrap.dedent —
# guarantees no line ever starts with leading whitespace, regardless of how
# deeply the call is nested in Python.
# ---------------------------------------------------------------------------
def html(markup: str) -> None:
    cleaned = "\n".join(line.strip() for line in markup.strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Model loading (cached so it only loads once per session, not per rerun)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_model():
    return load_model(MODEL_PATH)


def predict(img: Image.Image, model):
    resized = img.convert("RGB").resize(IMG_SIZE)
    x = np.asarray(resized, dtype="float32") / 255.0
    x = np.expand_dims(x, axis=0)
    preds = model.predict(x, verbose=0)[0]
    return preds


def img_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ---------------------------------------------------------------------------
# Styling — same token system as the Flask version (paper/teal/amber/brick)
# ---------------------------------------------------------------------------
html(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
      :root {
        --ink: #14231f; --ink-soft: #3c4a45; --paper: #eef1ec; --card: #fbfaf6;
        --teal: #1d6f63; --teal-deep: #0f4a42; --amber: #c98a2c;
        --brick: #b24b36; --sage: #6e8f7c; --line: #d7d2c4;
      }

      /* page shell */
      .stApp {
        background-color: var(--paper);
        background-image: linear-gradient(#e5e1d4 1px, transparent 1px),
                           linear-gradient(90deg, #e5e1d4 1px, transparent 1px);
        background-size: 32px 32px;
      }
      html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: var(--ink); }

      /* hide default streamlit chrome for a cleaner branded page */
      #MainMenu, footer, header { visibility: hidden; }
      .block-container { padding-top: 2.2rem; max-width: 1100px; }

      /* topbar */
      .cyto-topbar {
        display: flex; align-items: baseline; justify-content: space-between;
        border-bottom: 1px solid var(--line); padding-bottom: 14px; margin-bottom: 24px;
      }
      .cyto-brand { display: flex; align-items: baseline; gap: 10px; }
      .cyto-dot {
        width: 9px; height: 9px; border-radius: 50%; background: var(--sage);
        box-shadow: 0 0 0 3px rgba(110,143,124,0.18); display: inline-block;
      }
      .cyto-dot.busy {
        background: var(--amber); box-shadow: 0 0 0 3px rgba(201,138,44,0.2);
        animation: pulse 1.1s ease-in-out infinite;
      }
      @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
      .cyto-name {
        font-family: 'Space Grotesk', sans-serif; font-weight: 700;
        font-size: 20px; letter-spacing: 0.06em;
      }
      .cyto-sub { font-size: 13px; color: var(--ink-soft); }
      .cyto-meta { font-size: 12px; color: var(--ink-soft); }
      .cyto-meta b { font-family: 'IBM Plex Mono', monospace; color: var(--ink); font-weight: 500; }

      /* panel cards */
      .cyto-panel {
        background: var(--card); border: 1px solid var(--line); border-radius: 14px;
        padding: 20px 22px; box-shadow: 0 1px 2px rgba(20,35,31,0.04); height: 100%;
      }
      .cyto-panel-label {
        font-family: 'IBM Plex Mono', monospace; font-size: 11px; letter-spacing: 0.08em;
        color: var(--ink-soft); text-transform: uppercase; margin-bottom: 14px;
      }

      /* streamlit uploader restyled as a dropzone */
      [data-testid="stFileUploaderDropzone"] {
        background: repeating-linear-gradient(135deg, rgba(29,111,99,0.03), rgba(29,111,99,0.03) 8px, transparent 8px, transparent 16px);
        border: 1.5px dashed var(--line) !important;
        border-radius: 10px !important;
      }
      [data-testid="stFileUploaderDropzone"]:hover { border-color: var(--teal) !important; }
      [data-testid="stFileUploaderDropzoneInstructions"] svg { color: var(--teal); }

      /* buttons */
      .stButton > button {
        width: 100%; background: var(--teal-deep); color: #f2f6f4; border: none;
        border-radius: 8px; font-family: 'Space Grotesk', sans-serif; font-weight: 600;
        font-size: 14.5px; padding: 0.6rem 1rem;
      }
      .stButton > button:hover { background: var(--teal); color: #f2f6f4; }
      .stButton > button:disabled { background: var(--line); color: #9a978c; }

      /* scanline overlay on preview image while analyzing */
      .cyto-scan-wrap { position: relative; border-radius: 10px; overflow: hidden; line-height: 0; }
      .cyto-scan-wrap img { width: 100%; display: block; }
      .cyto-scanline {
        position: absolute; left: 0; right: 0; height: 2px; top: 0;
        background: linear-gradient(90deg, transparent, var(--teal) 15%, #7fe0c9 50%, var(--teal) 85%, transparent);
        box-shadow: 0 0 10px 1px rgba(127,224,201,0.7);
        animation: sweep 1.4s cubic-bezier(.6,0,.4,1) infinite;
      }
      @keyframes sweep { 0% { top: 0%; } 50% { top: calc(100% - 2px); } 100% { top: 0%; } }

      /* readout */
      .cyto-readout-empty { color: #9a978c; font-size: 14px; text-align: center; padding: 40px 10px; }
      .cyto-verdict {
        display: flex; align-items: baseline; justify-content: space-between;
        border-bottom: 1px solid var(--line); padding-bottom: 12px; margin-bottom: 12px;
      }
      .cyto-verdict-label { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 26px; }
      .cyto-verdict-conf { font-size: 13px; color: var(--ink-soft); font-family: 'IBM Plex Mono', monospace; }
      .cyto-note {
        font-size: 13.5px; color: var(--ink-soft); line-height: 1.5; margin: 0 0 18px;
      }
      .cyto-bar-row {
        display: grid; grid-template-columns: 84px 1fr 46px; align-items: center;
        gap: 10px; margin-bottom: 10px;
      }
      .cyto-bar-name { font-size: 13px; color: var(--ink-soft); }
      .cyto-bar-track { height: 8px; border-radius: 4px; background: #e5e1d4; overflow: hidden; }
      .cyto-bar-fill { height: 100%; border-radius: 4px; }
      .cyto-bar-pct {
        font-family: 'IBM Plex Mono', monospace; font-size: 12px; text-align: right; color: var(--ink-soft);
      }

      .cyto-disclaimer { font-size: 12px; color: var(--ink-soft); line-height: 1.6; margin-top: 28px; }
    </style>
    """
)

if "analyzing" not in st.session_state:
    st.session_state.analyzing = False
if "result" not in st.session_state:
    st.session_state.result = None

dot_class = "cyto-dot busy" if st.session_state.analyzing else "cyto-dot"
html(
    f"""
    <div class="cyto-topbar">
      <div class="cyto-brand">
        <span class="{dot_class}"></span>
        <span class="cyto-name">CYTOSCAN</span>
        <span class="cyto-sub">&nbsp;cytology screening assist</span>
      </div>
      <div class="cyto-meta">MODEL <b>v1 · 256×256</b></div>
    </div>
    """
)

col_scan, col_read = st.columns([1.1, 1], gap="medium")

# --------------------------------------------------------------------- scan
with col_scan:
    html('<div class="cyto-panel">')
    html('<div class="cyto-panel-label">01 · SPECIMEN</div>')

    uploaded_file = st.file_uploader(
        "Drop a cytology image here", type=["png", "jpg", "jpeg"], label_visibility="collapsed"
    )

    preview_slot = st.empty()
    img = None
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        preview_slot.image(img, use_container_width=True)

    analyze_clicked = st.button(
        "Analyze specimen", disabled=(uploaded_file is None), key="analyze_btn"
    )
    html("</div>")

# ------------------------------------------------------------------ analyze
if analyze_clicked and img is not None:
    st.session_state.analyzing = True
    b64 = img_to_b64(img)
    scan_markup = f"""
        <div class="cyto-scan-wrap">
          <img src="data:image/png;base64,{b64}">
          <div class="cyto-scanline"></div>
        </div>
        """
    cleaned_scan_markup = "\n".join(line.strip() for line in scan_markup.strip().splitlines())
    preview_slot.markdown(cleaned_scan_markup, unsafe_allow_html=True)
    model = get_model()
    preds = predict(img, model)
    st.session_state.result = {
        "label": CLASS_LABELS[int(np.argmax(preds))],
        "confidence": float(np.max(preds)),
        "probabilities": {c: float(p) for c, p in zip(CLASS_LABELS, preds)},
    }
    st.session_state.analyzing = False
    preview_slot.image(img, use_container_width=True)

# ------------------------------------------------------------------ readout
with col_read:
    html('<div class="cyto-panel">')
    html('<div class="cyto-panel-label">02 · READOUT</div>')

    result = st.session_state.result
    if result is None:
        html('<div class="cyto-readout-empty">Results appear here once a specimen is analyzed.</div>')
    else:
        label = result["label"]
        color = VERDICT_COLOR[label]
        html(
            f"""
            <div class="cyto-verdict">
              <span class="cyto-verdict-label" style="color:{color}">{label}</span>
              <span class="cyto-verdict-conf">{result['confidence']*100:.1f}% confidence</span>
            </div>
            <p class="cyto-note">{NOTES[label]}</p>
            """
        )
        for cls in CLASS_LABELS:
            pct = result["probabilities"][cls] * 100
            html(
                f"""
                <div class="cyto-bar-row">
                  <span class="cyto-bar-name">{cls}</span>
                  <div class="cyto-bar-track">
                    <div class="cyto-bar-fill" style="width:{pct:.1f}%; background:{BAR_COLOR[cls]}"></div>
                  </div>
                  <span class="cyto-bar-pct">{pct:.1f}%</span>
                </div>
                """
            )
    html("</div>")

html(
    """
    <p class="cyto-disclaimer">This tool is a screening aid trained on a limited dataset. It does not
    replace a pathologist's diagnosis — always confirm results with a qualified clinician.</p>
    """
)

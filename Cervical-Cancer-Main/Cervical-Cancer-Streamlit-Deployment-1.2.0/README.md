# Cytoscan — Streamlit Community Cloud deployment

This deployment keeps the existing Cytoscan HTML/CSS/JavaScript frontend and replaces only the Flask request layer with a Streamlit custom component bridge.

## Deploy

1. Push this folder to a GitHub repository.
2. In Streamlit Community Cloud, create a new app from that repository.
3. Set the main file path to `app.py`.
4. Deploy.

The model is loaded from `models/cervical_cancer_image_classifier.h5` with a relative path.

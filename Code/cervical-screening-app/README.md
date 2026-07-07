# Cytoscan — Cervical Cytology Screening Assist

A restyled front end and cleaned-up Flask backend for your cervical cancer
image classifier.

## What changed from your original version

- **Fixed mixed imports** — was mixing `keras.*` and `tensorflow.keras.*`;
  now everything goes through `tensorflow.keras`, which avoids the subtle
  bugs that come from two different Keras installations disagreeing with
  each other.
- **`/predict` now returns JSON** (label + confidence + full probability
  breakdown) instead of a bare string, so the front end can show a real
  readout instead of just a word.
- **Upload folder is created automatically** (`os.makedirs(..., exist_ok=True)`)
  and each uploaded file is deleted right after inference instead of piling
  up on disk.
- **File validation** — rejects empty submissions and non-image extensions
  before they ever reach the model.
- **New UI** — a two-panel "instrument" layout: drop/preview your specimen
  on the left, get a live readout with per-class probability bars on the
  right, with a scanning animation while inference runs.
- **Class order is documented in code** — the `CLASS_LABELS` list has a
  comment explaining *why* the order has to match `flow_from_directory`'s
  alphabetical indexing, so a future retrain doesn't reintroduce the same
  mismatch bug you hit before.

## Project structure

```
cervical-screening-app/
├── flask_app.py
├── requirements.txt
├── models/
│   └── cervical_cancer_image_classifier.h5
├── templates/
│   ├── base.html
│   └── index.html
├── static/
│   ├── css/main.css
│   └── js/main.js
└── uploads/            # created automatically, cleared after each prediction
```

## Running it

```bash
cd cervical-screening-app
python3 -m venv venv
source venv/bin/activate        # on Kali/Linux
pip install -r requirements.txt
python3 flask_app.py
```

Then open **http://127.0.0.1:5000/**.

## A note on the class labels

Your model's final layer has 3 softmax units. The order in `CLASS_LABELS`
(`Negative, Positive, Suspected`) assumes your training folders were named
so that alphabetical sorting produces that exact order. If you ever retrain
on a differently-named folder set, re-check `train_generator.class_indices`
in your training notebook and update `CLASS_LABELS` in `flask_app.py` to
match — this is the exact bug you ran into before, just documented now so
it's easy to catch.

## Notes / things you may want to add later

- There's no persistence layer — nothing is logged or stored. Fine for a
  demo/academic project; add a database if you want a history of scans.
- No auth. If you ever deploy this somewhere reachable, put it behind a
  login or at least rate-limit `/predict`.
- `app.run(debug=True)` is fine for local dev only — use a real WSGI server
  (gunicorn, gevent) for anything resembling production, same as your
  original `WSGIServer` import intended.

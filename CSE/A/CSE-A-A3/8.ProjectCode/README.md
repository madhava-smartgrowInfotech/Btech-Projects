# Intelligent Health Assistant — Multi-Disease Prediction System

A web application that predicts the risk of **Diabetes, Heart Disease,
Liver Disease, and Kidney Disease** from patient health parameters using
machine learning (Logistic Regression, Decision Tree, Random Forest, SVM).

## Features
- Four independent prediction modules (Diabetes / Heart / Liver / Kidney)
- Each disease is modeled with 4 ML algorithms; the best-performing model
  (by F1-score) is automatically selected and used for live predictions
- Clean, responsive web UI (Flask + HTML/CSS, no external dependencies)
- Shows prediction confidence and the model/accuracy used

## Project Structure
```
├── app.py                 # Flask web application (routes + prediction logic)
├── generate_data.py       # Generates the training datasets (data/*.csv)
├── train_models.py        # Trains & evaluates models, saves best ones
├── requirements.txt
├── data/                  # Generated CSV datasets (already included)
├── models/                # Trained models, scalers, feature lists (already included)
├── templates/             # HTML templates (index.html, predict.html)
└── static/style.css       # Stylesheet
```

## How to Run

1. **Install dependencies** (Python 3.9+ recommended):
   ```bash
   pip install -r requirements.txt
   ```

2. **(Optional) Regenerate data and retrain models.**
   Trained models are already included in `models/`, so this step is
   optional — only needed if you want to regenerate everything from
   scratch:
   ```bash
   python generate_data.py
   python train_models.py
   ```

3. **Run the web application:**
   ```bash
   python app.py
   ```

4. Open your browser at:
   ```
   http://127.0.0.1:5000/
   ```

5. Choose a condition (Diabetes / Heart / Liver / Kidney), fill in the
   patient's clinical values, and click **Predict Risk** to see the result.

## Notes
- The datasets used here are synthetically generated using medically
  informed value ranges and risk relationships (since the environment
  used to build this project had no internet access to download the
  original public datasets). The relationships between features and
  outcomes follow real clinical logic (e.g., high glucose + high BMI →
  higher diabetes risk), so the trained models behave realistically.
- If you have access to the original public clinical datasets (e.g. the
  PIMA Diabetes dataset, Cleveland Heart Disease dataset, Indian Liver
  Patient dataset, or Chronic Kidney Disease dataset), you can simply
  replace the corresponding CSV in `data/` with matching column names
  and rerun `train_models.py` to train on real data instead.
- This tool is for educational/demonstration purposes only and does not
  provide medical advice.

## Tech Stack
- Python, Flask
- scikit-learn (Logistic Regression, Decision Tree, Random Forest, SVM)
- pandas, numpy, joblib
- HTML5 / CSS3

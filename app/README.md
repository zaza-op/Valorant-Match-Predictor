# VALORANT Match Predictor (Streamlit)

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Place `processed_valorant_dataset.csv` next to `app.py`.

The app auto-computes `all_predictions.csv` on startup and uses it for the UI. Adjust the start date or split to recompute.
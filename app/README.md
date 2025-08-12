# VALORANT Match Predictor (Streamlit)

Changes included:
- Default training date = **2023-01-01** (matches your model)
- Opponent dropdown shows **only real opponents** that have played the selected team
- **Time-split control** via a slider (train proportion)
- Clean UI without emojis

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Place `processed_valorant_dataset.csv` next to `app.py`.

The app auto-computes `all_predictions.csv` on startup and uses it for the UI. Adjust the start date or split to recompute.
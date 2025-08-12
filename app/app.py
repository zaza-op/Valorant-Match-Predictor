import os
import pandas as pd
import numpy as np
import streamlit as st
from datetime import date
from model_utils import (
    FEATURES, prepare, train_model, compute_predictions_df, save_dataframe_csv
)

st.set_page_config(page_title="VALORANT Match Predictor", layout="wide")

# CSS
st.markdown("""
<style>
.block-container { font-size: 1.02rem; }
.small { font-size: 0.95rem; color: #697077; }

/* KPI cards: grey bg, white text */
.kpi {
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid #010001;     
  background: #262730;           
  color: #ffffff;                 /* white text by default inside card */
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
}
.kpi .label {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #ffffff;                 /* white label text */
  opacity: 0.9;
  margin-bottom: 6px;
}
.kpi .value {
  font-size: 1.5rem;             /* balanced with percentage text */
  font-weight: 800;
  line-height: 1.25;
  margin-bottom: 8px;
  color: #ffffff;                 /* white value text */
}

/* Probability meter (fading green) */
.meter {
  height: 10px;
  width: 100%;
  background: rgba(255,255,255,0.15);
  border-radius: 999px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.25);
}
.meter > span {
  display: block;
  height: 100%;
  border-radius: 999px;
  /* light → rich green */
  background: linear-gradient(90deg, #dcfce7 0%, #86efac 40%, #34d399 65%, #10b981 85%, #059669 100%);
}


/* Section title size */
.section-title { font-size: 1.15rem; font-weight: 800; margin: 1rem 0 0.5rem; }

/* Make tables slightly larger text */
.dataframe tbody, .dataframe thead { font-size: 0.98rem; }
</style>
""", unsafe_allow_html=True)

st.title("VALORANT Match Predictor")
st.caption("Logistic regression over interpretable features (map pool, R2, recent form, etc.).")

script_dir = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(script_dir, "processed_valorant_dataset.csv")
MASTER_PATH = "all_predictions.csv"

# Loading base data
if not os.path.exists(DATA_PATH):
    st.error(f"Couldn't find `{DATA_PATH}` in the current folder. Drop your CSV next to `app.py` and rerun.")
    st.stop()

df_raw = pd.read_csv(DATA_PATH)
if 'date' in df_raw.columns:
    df_raw['date'] = pd.to_datetime(df_raw['date'], errors='coerce')

with st.sidebar:
    st.header("Settings")
    # Default start date (model default)
    default_start = date(2023, 1, 1)
    start_date = st.date_input(
        "Training data start date",
        value=default_start,
        min_value=date(2020,1,1),
        max_value=date.today()
    )
    # Train proportion slider (split control)
    train_prop = st.slider(
        "Train proportion (time split)",
        min_value=0.50, max_value=0.90, value=0.75, step=0.01,
        help="Fraction of earliest dates used for training. Test = 1 - this value."
    )

@st.cache_data(show_spinner=False)
def _compute_master(df_raw: pd.DataFrame, start_date_str: str, train_prop: float):
    P = prepare(df_raw, start_date=start_date_str, train_prop=train_prop)
    model, metrics = train_model(P["Xtr"], P["ytr"], P["Xte"], P["yte"])
    preds_df = compute_predictions_df(P, model, metrics)
    # make master CSV so the UI can pull from it
    fname, csv_bytes = save_dataframe_csv(preds_df, filename=MASTER_PATH)
    with open(fname, "wb") as f:
        f.write(csv_bytes)
    return preds_df, metrics, P["split_date"]

with st.spinner("Computing master predictions..."):
    preds_df, metrics, split_date = _compute_master(df_raw, str(start_date), float(train_prop))

with st.sidebar:
    st.markdown("### Model Snapshot")
    st.write(f"- Train accuracy: **{metrics['train_acc']:.3f}**")
    st.write(f"- Test  accuracy: **{metrics['test_acc']:.3f}**")
    st.write(f"- Split date (time-based): **{split_date.date()}**")
    st.write(f"- Train proportion: **{train_prop:.2f}** (Test: **{1-train_prop:.2f}**)")
    st.write(f"- Rows (train / test): **{(preds_df['split']=='train').sum()} / {(preds_df['split']=='test').sum()}**")

# Interactive panel
st.header("Match Explorer")

# Team selector (unified list)
teams = pd.unique(pd.concat([preds_df["team_name"], preds_df["opponent"]], ignore_index=True).dropna())
all_teams = sorted(teams)
team = st.selectbox("Team", all_teams, index=0)

# Valid opponents vs selected team (either orientation)
mask_vs_team = (preds_df["team_name"] == team) | (preds_df["opponent"] == team)
df_vs_team = preds_df.loc[mask_vs_team]
opponents_a = df_vs_team.loc[df_vs_team["team_name"] == team, "opponent"]
opponents_b = df_vs_team.loc[df_vs_team["opponent"] == team, "team_name"]
valid_opponents = sorted(pd.unique(pd.concat([opponents_a, opponents_b], ignore_index=True).dropna()))

if not valid_opponents:
    st.info("No opponents found for this team in your dataset.")
    st.stop()

opponent = st.selectbox("Opponent", valid_opponents, index=0)

# Dates available for this pairing (either orientation)
pair_mask = (
    ((preds_df["team_name"] == team) & (preds_df["opponent"] == opponent)) |
    ((preds_df["team_name"] == opponent) & (preds_df["opponent"] == team))
)
pair_df = preds_df.loc[pair_mask].copy()
pair_df["date"] = pd.to_datetime(pair_df["date"], errors="coerce")
available_dates = sorted(pd.unique(pair_df["date"].dt.date.dropna()))
if not available_dates:
    st.info("No matches found between these teams in your dataset.")
    st.stop()

date_choice = st.selectbox("Match date", available_dates, index=len(available_dates)-1)

# Prefer orientation where selected team is 'team_name'; else fallback
row_mask_a = (
    (preds_df["team_name"] == team) &
    (preds_df["opponent"] == opponent) &
    (pd.to_datetime(preds_df["date"]).dt.date == date_choice)
)
row_mask_b = (
    (preds_df["team_name"] == opponent) &
    (preds_df["opponent"] == team) &
    (pd.to_datetime(preds_df["date"]).dt.date == date_choice)
)

if preds_df.loc[row_mask_a].shape[0] > 0:
    row = preds_df.loc[row_mask_a].iloc[0]
elif preds_df.loc[row_mask_b].shape[0] > 0:
    row = preds_df.loc[row_mask_b].iloc[0]
else:
    st.warning("Couldn't locate the selected match row. Check your dataset formatting.")
    st.stop()

# Predictions/actuals
proba = float(row["predicted_proba_win"])
pred_label = "Win" if int(row["predicted_class"]) == 1 else "Loss"
prob_pct = f"{proba*100:.1f}%"

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class="kpi">
      <div class="label">Predicted outcome</div>
      <div class="value">{team}: {pred_label}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi">
      <div class="label">Win probability</div>
      <div class="value">{prob_pct}</div>
      <div class="meter"><span style="width:{proba*100:.1f}%;"></span></div>
    </div>
    """, unsafe_allow_html=True)

actual_raw = str(row.get("result", "Unknown"))
if isinstance(actual_raw, str) and actual_raw.upper().startswith("W"):
    actual_label = "Win"
elif isinstance(actual_raw, str) and actual_raw.upper().startswith("L"):
    actual_label = "Loss"
else:
    actual_label = actual_raw

with col3:
    st.markdown(f"""
    <div class="kpi">
      <div class="label">Actual result</div>
      <div class="value">{actual_label}</div>
    </div>
    """, unsafe_allow_html=True)

# "Actual game here" link using match_url
match_url = row.get("match_url", None)
if pd.notna(match_url) and isinstance(match_url, str) and match_url.strip():
    st.markdown("#### Actual game here")
    st.markdown(f"[Open match link]({match_url})")

# Feature values section (horizontal row)
st.markdown('<div class="section-title">Feature values for this match</div>', unsafe_allow_html=True)
present_feats = [f for f in FEATURES if f in row.index]
table_cols = present_feats + ["team_name", "opponent", "date", "result"]
st.dataframe(row[table_cols].to_frame().T, use_container_width=True)

import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO
from datetime import datetime
from utils.cleaner import clean_data
from utils.features import compute_features
from utils.signals import detect_regime, generate_signal

st.set_page_config("Rule‑Based Intraday Option Signals", layout="wide")
st.title("📊 Rule‑Based Intraday Option Signal System")

# --- Sidebar controls ----------------------------------------------
rolling_n = st.sidebar.number_input("Rolling window", 3, 60, 5)
spread_cutoff = st.sidebar.slider("Max spread %", 0.0, 1.0, 0.2)
st.sidebar.markdown("Upload one or more 5‑min Option‑Chain CSVs below 👇")

# --- CSV file drop zone --------------------------------------------
uploaded_files = st.file_uploader(
    "Drop your option‑chain CSV files here (multiple allowed)",
    type=["csv"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("⬅️ Upload CSVs to start")
    st.stop()

# --- Parse & combine -----------------------------------------------
frames = []
for file in uploaded_files:
    try:
        name = file.name.replace(".csv","")
        ts = datetime.strptime(name.split("_")[-2]+"_"+name.split("_")[-1], "%d%m%Y_%H%M%S")
    except Exception:
        ts = datetime.now()
    df = pd.read_csv(file)
    df["timestamp"] = ts
    frames.append(df)

raw_df = pd.concat(frames, ignore_index=True)
st.success(f"✅ Loaded {len(uploaded_files)} file(s), {len(raw_df)} rows")

# --- Clean + feature calc ------------------------------------------
df = clean_data(raw_df, spread_cutoff)
df_feat = compute_features(df, rolling_n)
df_feat[["regime","bias"]] = df_feat.apply(detect_regime, axis=1, result_type="expand")
df_feat["signal"] = df_feat.apply(generate_signal, axis=1)

# --- Display summary ------------------------------------------------
st.subheader("Latest signals")
st.dataframe(df_feat.tail(10))

# --- Quick viz ------------------------------------------------------
import altair as alt
col1, col2 = st.columns(2)
with col1:
    chart1 = alt.Chart(df_feat.reset_index()).mark_line().encode(
        x="timestamp:T", y="PCR_OI:Q", color="regime:N"
    )
    st.altair_chart(chart1, use_container_width=True)

with col2:
    chart2 = alt.Chart(df_feat.reset_index()).mark_line().encode(
        x="timestamp:T", y="IV_skew:Q", color="bias:N"
    )
    st.altair_chart(chart2, use_container_width=True)

st.subheader("Full dataset")
st.dataframe(df_feat)

st.download_button(
    "⬇️ Download processed results",
    df_feat.to_csv().encode("utf-8"),
    file_name="signals_output.csv",
    mime="text/csv"
)

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from utils.loader import load_optionchain_files
from utils.cleaner import clean_data
from utils.features import compute_features
from utils.signals import detect_regime, generate_signal

st.set_page_config("Rule‑Based Intraday Option Signals", layout="wide")

st.title("📊 Rule‑Based Intraday Option Signal System")

# --- Sidebar --------------------------------------------------------
data_folder = Path(st.sidebar.text_input("Data folder", "data"))
rolling_n = st.sidebar.number_input("Rolling window", 3, 60, 5)
spread_cutoff = st.sidebar.slider("Max spread %", 0.0, 1.0, 0.2)
refresh = st.sidebar.button("🔄 Refresh Data")

# --- Load + clean ---------------------------------------------------
df = load_optionchain_files(data_folder)
if df.empty:
    st.warning("No CSVs found yet.")
    st.stop()

df = clean_data(df, spread_cutoff)
df_feat = compute_features(df, rolling_n)

# --- Regime & signal ------------------------------------------------
df_feat[["regime", "bias"]] = df_feat.apply(detect_regime, axis=1, result_type="expand")
df_feat["signal"] = df_feat.apply(generate_signal, axis=1)

st.subheader("Latest signals")
st.dataframe(df_feat.tail(10))

# --- Visualization --------------------------------------------------
import altair as alt

col1, col2 = st.columns(2)
with col1:
    fig1 = alt.Chart(df_feat.reset_index()).mark_line().encode(
        x="timestamp:T", y="PCR_OI:Q", color="regime:N"
    )
    st.altair_chart(fig1, use_container_width=True)

with col2:
    fig2 = alt.Chart(df_feat.reset_index()).mark_line().encode(
        x="timestamp:T", y="IV_skew:Q", color="bias:N"
    )
    st.altair_chart(fig2, use_container_width=True)

st.subheader("Full data")
st.dataframe(df_feat)

import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO
from datetime import datetime
import altair as alt

# -------------- CONFIG ---------------------------------------
st.set_page_config("Rule‑Based Intraday Option Signals", layout="wide")
st.title("📊 Rule‑Based Intraday Option Signal System")

# Sidebar controls
rolling_n = st.sidebar.number_input("Rolling window (minutes)", 3, 60, 5)
spread_cutoff = st.sidebar.slider("Max bid‑ask spread %", 0.0, 1.0, 0.2)
num_strikes = st.sidebar.number_input("Top strikes by OI", 1, 30, 6)
st.sidebar.markdown("Upload one or more **5‑min Option‑Chain CSVs** here 👇")

# -------------- CSV Upload -----------------------------------
uploaded_files = st.file_uploader(
    "Drop Option‑Chain CSV files (multiple allowed)",
    type=["csv"],
    accept_multiple_files=True
)
if not uploaded_files:
    st.info("⬅️ Upload CSVs to start.")
    st.stop()

frames = []
for file in uploaded_files:
    try:
        base = file.name.replace(".csv", "")
        ts = datetime.strptime(base.split("_")[-2] + "_" + base.split("_")[-1],
                               "%d%m%Y_%H%M%S")
    except Exception:
        ts = datetime.now()
    df = pd.read_csv(file)
    df["timestamp"] = ts
    frames.append(df)

raw_df = pd.concat(frames, ignore_index=True)
st.success(f"✅ Loaded {len(uploaded_files)} file(s), {len(raw_df)} rows total.")

# -------------- Clean Data -----------------------------------
def clean_data(df, spread_cutoff=0.2):
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df[(df["CE_buyPrice1"] > 0) & (df["CE_sellPrice1"] > 0)]
    df["mid_CE"] = (df["CE_buyPrice1"] + df["CE_sellPrice1"]) / 2
    df["mid_PE"] = (df["PE_buyPrice1"] + df["PE_sellPrice1"]) / 2
    df["spread_pct"] = abs(df["CE_sellPrice1"] - df["CE_buyPrice1"]) / df["mid_CE"]
    df = df[df["spread_pct"] < spread_cutoff]
    if "CE_expiryDate" in df.columns:
        df["CE_expiryDate"] = pd.to_datetime(df["CE_expiryDate"], errors="coerce")
        df["days_to_expiry"] = (df["CE_expiryDate"] - df["timestamp"]).dt.days
    else:
        df["days_to_expiry"] = 1
    df["days_to_expiry"].fillna(1, inplace=True)
    df["θ_adj_CE"] = df["CE_lastPrice"] / np.sqrt(df["days_to_expiry"].clip(lower=1))
    df["θ_adj_PE"] = df["PE_lastPrice"] / np.sqrt(df["days_to_expiry"].clip(lower=1))
    return df

df = clean_data(raw_df, spread_cutoff)

# -------------- Feature Computation (top‑N strikes) ----------
def compute_features(df, rolling_n=5, top_n=6):
    if {"CE_openInterest", "PE_openInterest", "CE_strikePrice"}.issubset(df.columns):
        df["total_OI"] = df["CE_openInterest"] + df["PE_openInterest"]
        top_strikes = (
            df.groupby("CE_strikePrice")["total_OI"]
              .mean()
              .nlargest(top_n)
              .index
              .tolist()
        )
        df = df[df["CE_strikePrice"].isin(top_strikes)]

    agg = df.groupby("timestamp").agg({
        "CE_lastPrice": "mean",
        "PE_lastPrice": "mean",
        "CE_changeinOpenInterest": "sum",
        "PE_changeinOpenInterest": "sum",
        "CE_totalTradedVolume": "sum",
        "PE_totalTradedVolume": "sum",
        "CE_impliedVolatility": "mean",
        "PE_impliedVolatility": "mean",
    })

    agg["ΔPrice_CE"] = agg["CE_lastPrice"].diff()
    agg["ΔPrice_PE"] = agg["PE_lastPrice"].diff()
    agg["ΔOI_CE"] = agg["CE_changeinOpenInterest"].diff()
    agg["ΔOI_PE"] = agg["PE_changeinOpenInterest"].diff()
    agg["IV_skew"] = agg["CE_impliedVolatility"] - agg["PE_impliedVolatility"]
    agg["ΔIV"] = agg["IV_skew"].diff()
    agg["PCR_OI"] = (
        agg["PE_changeinOpenInterest"] /
        agg["CE_changeinOpenInterest"].replace(0, np.nan)
    )
    total_vol = agg["CE_totalTradedVolume"] + agg["PE_totalTradedVolume"]
    agg["Volume_spike"] = total_vol / total_vol.rolling(rolling_n).mean()
    agg.fillna(0, inplace=True)
    return agg

df_feat = compute_features(df, rolling_n, num_strikes)

# -------------- Regime, Bias, Signal, Comment ----------------
def detect_regime(row):
    regime, bias = "quiet", "neutral"
    if row["ΔPrice_CE"] * row["ΔOI_CE"] > 0 and row["Volume_spike"] > 1:
        regime = "trend"
    elif abs(row["ΔPrice_CE"]) < 0.05 and abs(row["ΔOI_CE"]) < 1000:
        regime = "range"
    elif abs(row["ΔPrice_CE"]) > 0.2 and row["Volume_spike"] > 1.5 and row["ΔIV"] > 0:
        regime = "breakout"
    elif row["ΔPrice_CE"] > 0 and row["ΔOI_CE"] < 0 and row["ΔIV"] < 0:
        regime = "exhaustion"

    if row["PCR_OI"] < 0.8:
        bias = "bullish"
    elif row["PCR_OI"] > 1.2:
        bias = "bearish"
    return regime, bias

def generate_signal(row):
    if row["regime"] == "trend" and row["bias"] == "bullish":
        return "BUY_CALL"
    if row["regime"] == "trend" and row["bias"] == "bearish":
        return "BUY_PUT"
    if row["regime"] == "range":
        return "SELL_STRANGLE"
    if row["regime"] == "breakout":
        return "MOMENTUM_TRADE"
    if row["regime"] == "exhaustion":
        return "EXIT_POSITION"
    return "HOLD"

def conclusion_text(row):
    if row["bias"] == "bullish" and row["ΔOI_CE"] > row["ΔOI_PE"]:
        return "CE build‑up > PE build‑up → bullish skew forming."
    if row["regime"] == "breakout":
        return "Big volume spike on both calls & puts + IV rise → breakout conditions likely."
    if row["regime"] == "exhaustion":
        return "Price still rising but OI and IV both drop → long unwind, caution on upside."
    if row["regime"] == "trend" and row["ΔIV"] > 0:
        return "Rising IV + price surge → vol expansion; traders paying for protection."
    if row["PCR_OI"] > 0 and row.get("ΔPCR", 0) > 0.2:
        return "PCR climbing rapidly → put unwinding, optimism returning."
    if row["Volume_spike"] < 0.8 and abs(row["ΔIV"]) < 0.2:
        return "Flat prices + low IV + thin volume → stay out or short time premium."
    return ""

# apply computations
df_feat[["regime", "bias"]] = df_feat.apply(detect_regime, axis=1, result_type="expand")
df_feat["signal"] = df_feat.apply(generate_signal, axis=1)
df_feat["comment"] = df_feat.apply(conclusion_text, axis=1)

# -------------- Display section -------------------------------
st.subheader("Latest signals")
st.dataframe(df_feat.tail(10))

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



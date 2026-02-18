import pandas as pd
import numpy as np

def compute_features(df, rolling_n=5):
    # --- pick top 6 strikes by total OI (CE+PE)
    if {"CE_openInterest","PE_openInterest","CE_strikePrice"}.issubset(df.columns):
        df["total_OI"] = df["CE_openInterest"] + df["PE_openInterest"]
        top_strikes = (
            df.groupby("CE_strikePrice")["total_OI"]
              .mean()
              .nlargest(6)
              .index
              .tolist()
        )
        df = df[df["CE_strikePrice"].isin(top_strikes)]

    # --- aggregate over remaining strikes --------------------------------
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

    # --- derived features -------------------------------------------------
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

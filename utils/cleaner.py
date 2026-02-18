import pandas as pd
import numpy as np

def clean_data(df, spread_cutoff=0.2):
    df = df.copy()

    # --- sanity: ensure timestamp is datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # --- basic filters
    req = ["CE_buyPrice1","CE_sellPrice1","PE_buyPrice1","PE_sellPrice1"]
    available = [c for c in req if c in df.columns]
    df = df[(df[available] > 0).all(axis=1)]

    # --- mid & spread
    df["mid_CE"] = (df["CE_buyPrice1"] + df["CE_sellPrice1"]) / 2
    df["mid_PE"] = (df["PE_buyPrice1"] + df["PE_sellPrice1"]) / 2
    df["spread_pct"] = abs(df["CE_sellPrice1"] - df["CE_buyPrice1"]) / df["mid_CE"]
    df = df[df["spread_pct"] < spread_cutoff]

    # --- expiry safety + days‑to‑expiry
    if "CE_expiryDate" in df.columns:
        df["CE_expiryDate"] = pd.to_datetime(df["CE_expiryDate"], errors="coerce")
        df["days_to_expiry"] = (df["CE_expiryDate"] - df["timestamp"]).dt.days
    else:
        df["days_to_expiry"] = np.nan

    # avoid division by zero / NaN
    df["days_to_expiry"].fillna(1, inplace=True)

    # --- theta‑adjusted prices
    df["θ_adj_CE"] = df["CE_lastPrice"] / np.sqrt(df["days_to_expiry"].clip(lower=1))
    df["θ_adj_PE"] = df["PE_lastPrice"] / np.sqrt(df["days_to_expiry"].clip(lower=1))

    return df

import pandas as pd
import numpy as np

def compute_features(df, rolling_n=5):
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
    vol_t = agg["CE_totalTradedVolume"] + agg["PE_totalTradedVolume"]
    agg["Volume_spike"] = vol_t / vol_t.rolling(rolling_n).mean()
    agg.fillna(0, inplace=True)
    return agg



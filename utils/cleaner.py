def clean_data(df, spread_cutoff=0.2):
    df = df.copy()
    df = df[(df["CE_buyPrice1"] > 0) & (df["CE_sellPrice1"] > 0)]
    df["mid_CE"] = (df["CE_buyPrice1"] + df["CE_sellPrice1"]) / 2
    df["mid_PE"] = (df["PE_buyPrice1"] + df["PE_sellPrice1"]) / 2
    df["spread_pct"] = abs(df["CE_sellPrice1"] - df["CE_buyPrice1"]) / df["mid_CE"]
    df = df[df["spread_pct"] < spread_cutoff]
    df["days_to_expiry"] = (pd.to_datetime(df["CE_expiryDate"]) - df["timestamp"]).dt.days
    df["θ_adj_CE"] = df["CE_lastPrice"] / (df["days_to_expiry"]**0.5 + 1e-6)
    df["θ_adj_PE"] = df["PE_lastPrice"] / (df["days_to_expiry"]**0.5 + 1e-6)
    return df



def detect_regime(row):
    trend, bias = "quiet", "neutral"

    # regime
    if row["ΔPrice_CE"] * row["ΔOI_CE"] > 0 and row["Volume_spike"] > 1:
        trend = "trend"
    elif abs(row["ΔPrice_CE"]) < 0.05 and abs(row["ΔOI_CE"]) < 1000:
        trend = "range"
    elif abs(row["ΔPrice_CE"]) > 0.2 and row["Volume_spike"] > 1.5 and row["ΔIV"] > 0:
        trend = "breakout"
    elif row["ΔPrice_CE"] > 0 and row["ΔOI_CE"] < 0 and row["ΔIV"] < 0:
        trend = "exhaustion"

    # bias
    if row["PCR_OI"] < 0.8:
        bias = "bullish"
    elif row["PCR_OI"] > 1.2:
        bias = "bearish"

    return trend, bias


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

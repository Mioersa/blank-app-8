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
    # tie everything into plain‑English commentary
    if row["bias"] == "bullish" and row["ΔOI_CE"] > row["ΔOI_PE"]:
        return "CE build‑up > PE build‑up → bullish skew forming."
    if row["regime"] == "breakout":
        return "Big volume spike on both calls & puts + IV rise → breakout conditions likely."
    if row["regime"] == "exhaustion":
        return "Price still rising but OI and IV both drop → long unwind, caution on upside."
    if row["regime"] == "trend" and row["ΔIV"] > 0:
        return "Rising IV + price surge → vol expansion; traders paying for protection."
    if row["ΔPCR"] if "ΔPCR" in row else 0 > 0.2:
        return "PCR climbing rapidly → put unwinding, optimism returning."
    if row["Volume_spike"] < 0.8 and abs(row["ΔIV"]) < 0.2:
        return "Flat prices + low IV + thin volume → stay out or short time premium."
    return ""

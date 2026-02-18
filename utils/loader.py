import pandas as pd
from datetime import datetime

def load_optionchain_files(folder):
    files = sorted(list(folder.glob("*.csv")))
    frames = []
    for f in files:
        try:
            ts = datetime.strptime(f.stem.split("_")[-2] + "_" +
                                   f.stem.split("_")[-1], "%d%m%Y_%H%M%S")
        except Exception:
            continue
        df = pd.read_csv(f)
        df["timestamp"] = ts
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

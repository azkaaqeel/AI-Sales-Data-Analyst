import pandas as pd

def determine_period_type(df: pd.DataFrame, date_col: str) -> str:
    """Choose WoW if data span < 30 days, else MoM."""
    total_days = (df[date_col].max() - df[date_col].min()).days
    return "WoW" if total_days < 30 else "MoM"


def add_period_column(df: pd.DataFrame, date_col: str, period_type: str) -> pd.DataFrame:
    """Add a 'period' column based on WoW or MoM grouping."""
    df = df.copy()
    if period_type == "WoW":
        df["period"] = df[date_col].dt.to_period("W").apply(lambda r: r.start_time)
    else:
        df["period"] = df[date_col].dt.to_period("M").apply(lambda r: r.start_time)
    return df
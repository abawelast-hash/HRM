"""ShamIn validation utilities — adapted from ACTION-main."""
import pandas as pd
import numpy as np


def validate_dataframe(df: pd.DataFrame, required_columns: list, name: str = "DataFrame"):
    """Validate that a DataFrame has required columns and no critical issues."""
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")

    if df.empty:
        raise ValueError(f"{name} is empty")

    return True


def check_nan_ratio(df: pd.DataFrame, threshold: float = 0.5) -> dict:
    """Check NaN ratios per column. Returns columns exceeding threshold."""
    nan_ratios = df.isnull().mean()
    problematic = nan_ratios[nan_ratios > threshold]
    return problematic.to_dict()


def validate_price_range(price: float, min_val: float = 100, max_val: float = 1_000_000) -> bool:
    """Validate that a SYP price is within a reasonable range."""
    return min_val <= price <= max_val


def detect_outliers_iqr(series: pd.Series, factor: float = 1.5) -> pd.Series:
    """Detect outliers using IQR method. Returns boolean mask."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    return (series < lower) | (series > upper)


def validate_time_continuity(timestamps: pd.Series, expected_freq: str = "H", max_gap_hours: int = 72) -> list:
    """Find gaps in time series exceeding max_gap_hours."""
    sorted_ts = timestamps.sort_values()
    diffs = sorted_ts.diff().dropna()
    max_gap = pd.Timedelta(hours=max_gap_hours)
    gaps = diffs[diffs > max_gap]
    return [(sorted_ts.iloc[i], sorted_ts.iloc[i + 1], gap) for i, gap in gaps.items()]

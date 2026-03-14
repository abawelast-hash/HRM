"""Time-series interpolation for gap filling."""
import pandas as pd
import numpy as np
from typing import Optional


class Interpolator:
    """Fill gaps in time-series data."""

    def __init__(self, method: str = "quadratic", max_gap_hours: int = 72):
        self.method = method
        self.max_gap_hours = max_gap_hours

    def interpolate(self, df: pd.DataFrame, time_col: str = "timestamp",
                    value_col: str = "price", freq: str = "H") -> pd.DataFrame:
        """
        Interpolate missing values in time series.
        Flags interpolated values with 'is_interpolated' column.
        """
        df = df.copy()
        df[time_col] = pd.to_datetime(df[time_col])
        df = df.set_index(time_col).sort_index()

        # Resample to regular frequency
        full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq=freq)
        df = df.reindex(full_range)

        # Flag which values are interpolated
        df['is_interpolated'] = df[value_col].isna()

        # Find gaps exceeding max_gap_hours — don't interpolate those
        gaps = df[value_col].isna()
        gap_groups = gaps.ne(gaps.shift()).cumsum()
        gap_sizes = gaps.groupby(gap_groups).transform('sum')
        too_large = gap_sizes > self.max_gap_hours
        df.loc[too_large & gaps, 'is_interpolated'] = False  # mark as still missing

        # Interpolate within acceptable gaps
        df[value_col] = df[value_col].interpolate(method=self.method, limit=self.max_gap_hours)

        df.index.name = time_col
        return df.reset_index()

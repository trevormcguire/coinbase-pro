from typing import List

import pandas as pd


def candles_to_dataframe(ohlc_data: List[list]) -> pd.DataFrame:
    """
    returns the output of Public().get_candles() as a pandas df
    """
    column_names = ["timestamp", "low", "high", "open", "close", "volume"]
    data = pd.DataFrame(ohlc_data, columns=column_names)
    data["timestamp"] = pd.to_datetime(data["timestamp"], unit="s", origin="unix")
    data.sort_values(by="timestamp", inplace=True)
    data = data.reset_index(drop=True)
    return data


import pandas as pd
import yfinance as yf


def fetch_ohlcv(ticker: str, days: int = 756) -> pd.DataFrame:
    df = yf.download(ticker, period=f'{days}d', interval='1d',
                     progress=False, auto_adjust=True)
    df.index = pd.to_datetime(df.index)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    return df[['open', 'high', 'low', 'close', 'volume']].dropna()


def fetch_close(ticker: str, days: int = 500) -> pd.Series:
    df = fetch_ohlcv(ticker, days)
    return df['close'].rename(ticker)


def fetch_vix(days: int = 756) -> pd.Series:
    df = yf.download('^VIX', period=f'{days}d', interval='1d',
                     progress=False, auto_adjust=True)
    df.index = pd.to_datetime(df.index)
    return df['Close'].squeeze().dropna().rename('VIX')

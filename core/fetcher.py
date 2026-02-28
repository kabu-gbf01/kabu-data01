import time
import pandas as pd
import yfinance as yf
from config import CHUNK_SIZE, SLEEP_SEC, PERIOD, JPX_MASTER_URL, MARKET_MAP, CHG_COL


def load_stock_list(markets: list) -> pd.DataFrame:
    master = pd.read_excel(JPX_MASTER_URL, dtype=str)
    market_names = [MARKET_MAP[m] for m in markets if m in MARKET_MAP]
    filtered = master[master["市場・商品区分"].isin(market_names)].copy()
    filtered["Ticker"] = filtered["コード"].str.zfill(4) + ".T"
    return filtered


def fetch_quotes(stock_df: pd.DataFrame, progress_callback=None) -> pd.DataFrame:
    tickers = stock_df["Ticker"].tolist()
    records = []
    n = len(tickers)

    for i in range(0, n, CHUNK_SIZE):
        chunk = tickers[i: i + CHUNK_SIZE]
        try:
            data = yf.download(
                chunk, period=PERIOD, interval="1d",
                group_by="ticker", auto_adjust=False,
                progress=False, threads=True,
            )
        except Exception as e:
            print(f"download error: {e}")
            time.sleep(SLEEP_SEC * 2)
            if progress_callback:
                progress_callback(min(i + CHUNK_SIZE, n), n, f"Error: {e}")
            continue

        for t in chunk:
            code = t.replace(".T", "")
            try:
                dft = data[t].dropna()
                if dft.empty:
                    continue
                row = dft.iloc[-1]
                prev_close = float(dft.iloc[-2]["Close"]) if len(dft) >= 2 else None
                records.append({
                    "Code":      code,
                    "Ticker":    t,
                    "Open":      float(row["Open"]),
                    "High":      float(row["High"]),
                    "Low":       float(row["Low"]),
                    "Close":     float(row["Close"]),
                    "Volume":    float(row["Volume"]),
                    "PrevClose": prev_close,
                })
            except Exception:
                continue

        if progress_callback:
            progress_callback(min(i + CHUNK_SIZE, n), n, f"{chunk[0]} ...")
        if i + CHUNK_SIZE < n:
            time.sleep(SLEEP_SEC)

    return pd.DataFrame(records)


def build_result_df(stock_df: pd.DataFrame, quotes_df: pd.DataFrame) -> pd.DataFrame:
    df = quotes_df.merge(
        stock_df[["コード", "銘柄名", "市場・商品区分", "17業種区分"]],
        left_on="Code", right_on="コード", how="left",
    )
    df.drop(columns=["コード"], inplace=True)
    df.rename(columns={
        "銘柄名": "CompanyName",
        "市場・商品区分": "Market",
        "17業種区分": "Sector17",
    }, inplace=True)

    # ── 基本指標 ──────────────────────────────────────────────
    df[CHG_COL]          = ((df["Close"] - df["Open"])     / df["Open"]      * 100).round(2)
    df["前日比(%)"]      = ((df["Close"] - df["PrevClose"]) / df["PrevClose"] * 100).round(2)
    df["振れ幅(%)"]      = ((df["High"]  - df["Low"])      / df["Open"]      * 100).round(2)

    rng = (df["High"] - df["Low"]).replace(0, 1e-9)
    df["レンジ位置"]     = ((df["Close"] - df["Low"])  / rng).round(3)
    df["上ヒゲ比"]       = ((df["High"]  - df["Close"]) / rng).round(3)

    # ── VWAP・売買代金 ─────────────────────────────────────────
    df["VWAP"]           = ((df["High"] + df["Low"] + df["Close"]) / 3).round(0)
    df["売買代金(百万円)"] = (df["VWAP"] * df["Volume"] / 1_000_000).round(1)
    df["終値/VWAP"]      = (df["Close"] / df["VWAP"]).round(3)

    # ── セクター系指標 ─────────────────────────────────────────
    df["全体順位"]         = df[CHG_COL].rank(ascending=False, method="min").astype(int)
    df["セクター内順位"]   = (
        df.groupby("Sector17")[CHG_COL].rank(ascending=False, method="min").astype(int)
    )
    df["セクター銘柄数"]   = df.groupby("Sector17")["Code"].transform("count")
    df["セクター内%"]      = (df["セクター内順位"] / df["セクター銘柄数"]).round(3)
    df["vsセクター"]       = (
        df[CHG_COL] - df.groupby("Sector17")[CHG_COL].transform("mean")
    ).round(2)

    return df

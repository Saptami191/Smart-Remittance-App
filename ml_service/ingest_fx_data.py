"""Fetch historical FX data from Frankfurter v2 and save it for training."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://api.frankfurter.dev/v2/rates"
DEFAULT_START = "2021-01-01"


def fetch_rates(base: str, symbol: str, start: str, end: str) -> pd.DataFrame:
    response = requests.get(
        BASE_URL,
        params={
            "base": base,
            "quotes": symbol,
            "from": start,
            "to": end,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()

    if not isinstance(payload, list):
        raise RuntimeError("Frankfurter returned an unexpected response format")

    rows = [
        {"date": item["date"], "exchange_rate": item["rate"]}
        for item in payload
        if item.get("base") == base
        and item.get("quote") == symbol
        and item.get("rate") is not None
    ]

    if not rows:
        raise RuntimeError(f"No {base}/{symbol} rates returned by Frankfurter")

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.date
    df["exchange_rate"] = pd.to_numeric(df["exchange_rate"], errors="coerce")
    df = df.dropna().drop_duplicates("date").sort_values("date")

    if (df["exchange_rate"] <= 0).any():
        raise ValueError("Dataset contains non-positive exchange rates")

    expected_start = date.fromisoformat(start)
    expected_end = date.fromisoformat(end)
    if df["date"].min() > expected_start:
        print(
            "Warning: source has no observation at the requested start date; "
            f"first available observation is {df['date'].min()}"
        )
    if df["date"].max() > expected_end:
        raise ValueError("Source returned data beyond the requested end date")

    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch historical FX rates")
    parser.add_argument("--base", default="USD")
    parser.add_argument("--symbol", default="INR")
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=date.today().isoformat())
    parser.add_argument("--output", default="data/raw/forex_rates.csv")
    args = parser.parse_args()

    df = fetch_rates(args.base.upper(), args.symbol.upper(), args.start, args.end)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)

    print(f"Saved {len(df)} observations to {output}")
    print(f"Range: {df['date'].min()} -> {df['date'].max()}")


if __name__ == "__main__":
    main()

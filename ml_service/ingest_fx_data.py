"""Fetch historical FX data from Frankfurter and save it for training."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://api.frankfurter.dev/v1"
DEFAULT_START = "2021-01-01"


def fetch_rates(base: str, symbol: str, start: str, end: str) -> pd.DataFrame:
    url = f"{BASE_URL}/{start}..{end}"
    response = requests.get(
        url,
        params={"base": base, "symbols": symbol},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()

    rates = payload.get("rates", {})
    rows = [
        {"date": day, "exchange_rate": values[symbol]}
        for day, values in rates.items()
        if symbol in values
    ]

    if not rows:
        raise RuntimeError(f"No {base}/{symbol} rates returned by Frankfurter")

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.date
    df["exchange_rate"] = pd.to_numeric(df["exchange_rate"], errors="coerce")
    df = df.dropna().drop_duplicates("date").sort_values("date")

    if (df["exchange_rate"] <= 0).any():
        raise ValueError("Dataset contains non-positive exchange rates")

    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch historical FX rates")
    parser.add_argument("--base", default="USD")
    parser.add_argument("--symbol", default="INR")
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=date.today().isoformat())
    parser.add_argument(
        "--output",
        default="data/raw/forex_rates.csv",
    )
    args = parser.parse_args()

    df = fetch_rates(args.base.upper(), args.symbol.upper(), args.start, args.end)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)

    print(f"Saved {len(df)} observations to {output}")
    print(f"Range: {df['date'].min()} -> {df['date'].max()}")


if __name__ == "__main__":
    main()

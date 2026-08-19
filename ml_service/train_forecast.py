"""Train and backtest the SmartRemit FX forecasting model offline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error

DEFAULT_DATA = "data/raw/forex_rates.csv"
DEFAULT_MODEL = "ml_model/forecast_model.joblib"
DEFAULT_METADATA = "ml_model/forecast_model_metadata.json"


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"date", "exchange_rate"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = df[["date", "exchange_rate"]].copy()
    df["ds"] = pd.to_datetime(df.pop("date"), errors="coerce")
    df["y"] = pd.to_numeric(df.pop("exchange_rate"), errors="coerce")
    df = df.dropna().drop_duplicates("ds").sort_values("ds")

    if len(df) < 100:
        raise ValueError("At least 100 observations are required for training")
    if (df["y"] <= 0).any():
        raise ValueError("Exchange rates must be positive")

    return df[["ds", "y"]].reset_index(drop=True)


def backtest(df: pd.DataFrame, validation_fraction: float) -> dict[str, float]:
    split = int(len(df) * (1 - validation_fraction))
    if split < 60 or len(df) - split < 20:
        raise ValueError("Dataset is too small for the requested validation split")

    train = df.iloc[:split].copy()
    test = df.iloc[split:].copy()

    model = Prophet(daily_seasonality=True, interval_width=0.95)
    model.fit(train)

    # Predict on the actual validation dates. This avoids inventing weekend
    # observations when the source dataset contains business-day FX rates.
    forecast = model.predict(test[["ds"]])
    predicted = forecast["yhat"].to_numpy()
    actual = test["y"].to_numpy()

    mae = mean_absolute_error(actual, predicted)
    rmse = mean_squared_error(actual, predicted) ** 0.5
    mape = abs((actual - predicted) / actual).mean() * 100

    # Naive baseline: every validation value equals the last training value.
    baseline = [train["y"].iloc[-1]] * len(test)
    baseline_mae = mean_absolute_error(actual, baseline)

    return {
        "validation_observations": len(test),
        "mae": round(float(mae), 6),
        "rmse": round(float(rmse), 6),
        "mape_percent": round(float(mape), 4),
        "naive_baseline_mae": round(float(baseline_mae), 6),
        "beats_naive_baseline": bool(mae < baseline_mae),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train SmartRemit FX forecast model")
    parser.add_argument("--data", default=DEFAULT_DATA)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--metadata", default=DEFAULT_METADATA)
    parser.add_argument("--validation-fraction", type=float, default=0.2)
    parser.add_argument("--from-currency", default="USD")
    parser.add_argument("--to-currency", default="INR")
    args = parser.parse_args()

    if not 0.1 <= args.validation_fraction <= 0.4:
        raise ValueError("validation-fraction must be between 0.1 and 0.4")

    df = load_data(args.data)
    metrics = backtest(df, args.validation_fraction)

    if not metrics["beats_naive_baseline"]:
        raise RuntimeError(
            "Prophet did not beat the naive baseline; refusing to promote the model"
        )

    final_model = Prophet(daily_seasonality=True, interval_width=0.95)
    final_model.fit(df)

    model_path = Path(args.model)
    metadata_path = Path(args.metadata)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(final_model, model_path)
    metadata = {
        "model_type": "prophet",
        "from_currency": args.from_currency.upper(),
        "to_currency": args.to_currency.upper(),
        "training_observations": len(df),
        "training_start": df["ds"].min().date().isoformat(),
        "training_end": df["ds"].max().date().isoformat(),
        "validation_fraction": args.validation_fraction,
        "metrics": metrics,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(json.dumps(metadata, indent=2))
    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    main()

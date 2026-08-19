"""Train and validate the SmartRemit FX forecasting model offline."""

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

    if len(df) < 200:
        raise ValueError("At least 200 observations are required for training")
    if (df["y"] <= 0).any():
        raise ValueError("Exchange rates must be positive")

    return df[["ds", "y"]].reset_index(drop=True)


def evaluate_window(train: pd.DataFrame, test: pd.DataFrame) -> dict[str, float]:
    model = Prophet(daily_seasonality=True, interval_width=0.95)
    model.fit(train)

    forecast = model.predict(test[["ds"]])
    predicted = forecast["yhat"].to_numpy()
    actual = test["y"].to_numpy()

    mae = mean_absolute_error(actual, predicted)
    rmse = mean_squared_error(actual, predicted) ** 0.5
    mape = abs((actual - predicted) / actual).mean() * 100

    baseline = [train["y"].iloc[-1]] * len(test)
    baseline_mae = mean_absolute_error(actual, baseline)

    return {
        "observations": len(test),
        "mae": float(mae),
        "rmse": float(rmse),
        "mape_percent": float(mape),
        "naive_baseline_mae": float(baseline_mae),
        "beats_naive_baseline": bool(mae < baseline_mae),
    }


def rolling_backtest(df: pd.DataFrame, folds: int, horizon: int) -> dict:
    if folds < 2:
        raise ValueError("At least 2 backtest folds are required")
    if horizon < 5:
        raise ValueError("Backtest horizon must be at least 5 observations")

    minimum_training = 200
    required = minimum_training + folds * horizon
    if len(df) < required:
        raise ValueError(
            f"Need at least {required} observations for {folds} folds of {horizon} observations"
        )

    results: list[dict] = []
    first_test_start = len(df) - folds * horizon

    for fold in range(folds):
        test_start = first_test_start + fold * horizon
        test_end = test_start + horizon
        train = df.iloc[:test_start].copy()
        test = df.iloc[test_start:test_end].copy()

        metrics = evaluate_window(train, test)
        metrics.update(
            {
                "fold": fold + 1,
                "train_end": train["ds"].iloc[-1].date().isoformat(),
                "test_start": test["ds"].iloc[0].date().isoformat(),
                "test_end": test["ds"].iloc[-1].date().isoformat(),
            }
        )
        results.append(metrics)

    mean_mae = sum(item["mae"] for item in results) / len(results)
    mean_rmse = sum(item["rmse"] for item in results) / len(results)
    mean_mape = sum(item["mape_percent"] for item in results) / len(results)
    mean_baseline_mae = sum(item["naive_baseline_mae"] for item in results) / len(results)
    folds_won = sum(item["beats_naive_baseline"] for item in results)

    return {
        "folds": results,
        "fold_count": len(results),
        "horizon_observations": horizon,
        "folds_won": folds_won,
        "mean_mae": round(mean_mae, 6),
        "mean_rmse": round(mean_rmse, 6),
        "mean_mape_percent": round(mean_mape, 4),
        "mean_naive_baseline_mae": round(mean_baseline_mae, 6),
        "beats_naive_baseline": bool(mean_mae < mean_baseline_mae),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and validate SmartRemit FX forecast model")
    parser.add_argument("--data", default=DEFAULT_DATA)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--metadata", default=DEFAULT_METADATA)
    parser.add_argument("--folds", type=int, default=4)
    parser.add_argument("--horizon", type=int, default=30)
    parser.add_argument("--from-currency", default="USD")
    parser.add_argument("--to-currency", default="INR")
    args = parser.parse_args()

    df = load_data(args.data)
    backtest_metrics = rolling_backtest(df, args.folds, args.horizon)

    # Always print the complete diagnostics before deciding whether to promote.
    metadata = {
        "model_type": "prophet",
        "from_currency": args.from_currency.upper(),
        "to_currency": args.to_currency.upper(),
        "training_observations": len(df),
        "training_start": df["ds"].min().date().isoformat(),
        "training_end": df["ds"].max().date().isoformat(),
        "backtest": backtest_metrics,
    }
    print(json.dumps(metadata, indent=2))

    if not backtest_metrics["beats_naive_baseline"]:
        raise RuntimeError(
            "Prophet did not beat the naive baseline across rolling backtests; refusing to promote the model"
        )

    final_model = Prophet(daily_seasonality=True, interval_width=0.95)
    final_model.fit(df)

    model_path = Path(args.model)
    metadata_path = Path(args.metadata)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(final_model, model_path)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    main()

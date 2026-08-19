"""Evaluate FX forecasting candidates and promote only a validated winner."""

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
    actual = test["y"].to_numpy()

    # Persistence baseline: next observations equal the latest observed rate.
    naive_pred = [train["y"].iloc[-1]] * len(test)
    naive_mae = mean_absolute_error(actual, naive_pred)

    # Seven-observation moving-average baseline.
    window = min(7, len(train))
    moving_avg_pred = [train["y"].iloc[-window:].mean()] * len(test)
    moving_avg_mae = mean_absolute_error(actual, moving_avg_pred)

    # Exponential smoothing with a fixed, reproducible alpha.
    alpha = 0.3
    level = float(train["y"].iloc[0])
    for value in train["y"].iloc[1:]:
        level = alpha * float(value) + (1 - alpha) * level
    exp_pred = [level] * len(test)
    exp_mae = mean_absolute_error(actual, exp_pred)

    prophet = Prophet(daily_seasonality=True, interval_width=0.95)
    prophet.fit(train)
    forecast = prophet.predict(test[["ds"]])
    prophet_pred = forecast["yhat"].to_numpy()
    prophet_mae = mean_absolute_error(actual, prophet_pred)
    prophet_rmse = mean_squared_error(actual, prophet_pred) ** 0.5
    prophet_mape = abs((actual - prophet_pred) / actual).mean() * 100

    candidates = {
        "naive": float(naive_mae),
        "moving_average_7": float(moving_avg_mae),
        "exponential_smoothing": float(exp_mae),
        "prophet": float(prophet_mae),
    }
    winner = min(candidates, key=candidates.get)

    return {
        "observations": len(test),
        "mae": round(float(prophet_mae), 6),
        "rmse": round(float(prophet_rmse), 6),
        "mape_percent": round(float(prophet_mape), 4),
        "naive_baseline_mae": round(float(naive_mae), 6),
        "candidate_mae": {name: round(value, 6) for name, value in candidates.items()},
        "winner": winner,
    }


def rolling_backtest(df: pd.DataFrame, folds: int, horizon: int) -> dict:
    if folds < 2:
        raise ValueError("At least 2 backtest folds are required")
    if horizon < 5:
        raise ValueError("Backtest horizon must be at least 5 observations")

    minimum_training = 200
    required = minimum_training + folds * horizon
    if len(df) < required:
        raise ValueError(f"Need at least {required} observations")

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

    candidates = ["naive", "moving_average_7", "exponential_smoothing", "prophet"]
    aggregate = {
        name: sum(item["candidate_mae"][name] for item in results) / len(results)
        for name in candidates
    }
    fold_wins = {
        name: sum(item["winner"] == name for item in results) for name in candidates
    }
    winner = min(aggregate, key=aggregate.get)

    return {
        "folds": results,
        "fold_count": len(results),
        "horizon_observations": horizon,
        "mean_candidate_mae": {
            name: round(value, 6) for name, value in aggregate.items()
        },
        "fold_wins": fold_wins,
        "selected_candidate": winner,
        "beats_naive_baseline": bool(aggregate[winner] < aggregate["naive"]),
    }


def train_selected_model(df: pd.DataFrame, selected: str):
    if selected == "prophet":
        model = Prophet(daily_seasonality=True, interval_width=0.95)
        model.fit(df)
        return model
    if selected in {"naive", "moving_average_7", "exponential_smoothing"}:
        # Store parameters instead of pretending these baselines are ML models.
        if selected == "naive":
            return {"type": selected, "value": float(df["y"].iloc[-1])}
        if selected == "moving_average_7":
            return {"type": selected, "value": float(df["y"].iloc[-7:].mean())}
        alpha = 0.3
        level = float(df["y"].iloc[0])
        for value in df["y"].iloc[1:]:
            level = alpha * float(value) + (1 - alpha) * level
        return {"type": selected, "alpha": alpha, "value": level}
    raise ValueError(f"Unknown model candidate: {selected}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate and train SmartRemit FX model")
    parser.add_argument("--data", default=DEFAULT_DATA)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--metadata", default=DEFAULT_METADATA)
    parser.add_argument("--folds", type=int, default=4)
    parser.add_argument("--horizon", type=int, default=30)
    parser.add_argument("--from-currency", default="USD")
    parser.add_argument("--to-currency", default="INR")
    args = parser.parse_args()

    df = load_data(args.data)
    backtest = rolling_backtest(df, args.folds, args.horizon)

    print(json.dumps(backtest, indent=2))

    selected = backtest["selected_candidate"]
    if not backtest["beats_naive_baseline"]:
        print("No candidate beats the naive baseline; no model will be promoted.")
        metadata = {
            "status": "rejected",
            "model_type": None,
            "from_currency": args.from_currency.upper(),
            "to_currency": args.to_currency.upper(),
            "training_observations": len(df),
            "training_start": df["ds"].min().date().isoformat(),
            "training_end": df["ds"].max().date().isoformat(),
            "backtest": backtest,
        }
        Path(args.metadata).parent.mkdir(parents=True, exist_ok=True)
        Path(args.metadata).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return

    model = train_selected_model(df, selected)
    model_path = Path(args.model)
    metadata_path = Path(args.metadata)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)

    metadata = {
        "status": "promoted",
        "model_type": selected,
        "from_currency": args.from_currency.upper(),
        "to_currency": args.to_currency.upper(),
        "training_observations": len(df),
        "training_start": df["ds"].min().date().isoformat(),
        "training_end": df["ds"].max().date().isoformat(),
        "backtest": backtest,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    print(f"Promoted {selected} model to {model_path}")


if __name__ == "__main__":
    main()

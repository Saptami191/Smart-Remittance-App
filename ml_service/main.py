from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timedelta
from pathlib import Path

import joblib
import pandas as pd
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SmartRemit ML Service")

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR.parent / "ml_model" / "forecast_model.joblib"
METADATA_PATH = BASE_DIR.parent / "ml_model" / "forecast_model_metadata.json"
FRAUD_MODEL_PATH = BASE_DIR.parent / "ml_model" / "fraud_model.pkl"
LEGACY_FRAUD_MODEL_PATH = BASE_DIR.parent / "fraud_model.pkl"

# Models are loaded once per process. Training never happens on a user request.
forecast_model = None
forecast_metadata: dict = {}
forecast_cache: dict[str, dict] = {}
fraud_model = None


def score_route(fee: float, rate: float, time: float, reliability: float) -> float:
    return (rate * reliability) - (fee * 0.5) - (time / 1000)


class Route(BaseModel):
    id: int
    fee: float = Field(ge=0)
    exchange_rate: float = Field(gt=0)
    time: float = Field(ge=0)
    reliability: float = Field(ge=0, le=1)


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/ready")
async def ready():
    if not MODEL_PATH.exists():
        raise HTTPException(status_code=503, detail="Forecast model is not available")
    return {"status": "ready"}


@app.post("/predict-route")
async def predict_route(routes: list[Route]):
    logger.info("Predicting route for %d options", len(routes))
    if not routes:
        raise HTTPException(status_code=400, detail="No routes provided")

    df = pd.DataFrame([r.model_dump() for r in routes])
    df["score"] = df.apply(
        lambda row: score_route(
            row["fee"], row["exchange_rate"], row["time"], row["reliability"]
        ),
        axis=1,
    )
    best = df.loc[df["score"].idxmax()]
    return best.to_dict()


class ForecastRequest(BaseModel):
    from_curr: str = Field(default="USD", min_length=3, max_length=3)
    to_curr: str = Field(default="INR", min_length=3, max_length=3)
    amount: float = Field(default=1000.0, gt=0, le=10_000_000)
    days: int = Field(default=7, ge=1, le=30)


def get_forecast_model():
    global forecast_model, forecast_metadata

    if forecast_model is None:
        if not MODEL_PATH.exists():
            raise HTTPException(
                status_code=503,
                detail="Forecast model is unavailable. Run train_forecast.py first.",
            )
        try:
            forecast_model = joblib.load(MODEL_PATH)
            if METADATA_PATH.exists():
                forecast_metadata = json.loads(
                    METADATA_PATH.read_text(encoding="utf-8")
                )
            logger.info("Loaded forecast model from %s", MODEL_PATH)
        except Exception as exc:
            logger.exception("Failed to load forecast model")
            raise HTTPException(
                status_code=503, detail="Forecast model could not be loaded"
            ) from exc

    return forecast_model


@app.post("/forecast")
async def forecast_rates(req: ForecastRequest = Body(...)):
    global forecast_cache

    from_curr = req.from_curr.upper()
    to_curr = req.to_curr.upper()
    currency_pair = f"{from_curr}{to_curr}"

    trained_pair = "".join(
        [
            str(forecast_metadata.get("from_currency", "")),
            str(forecast_metadata.get("to_currency", "")),
        ]
    )
    if trained_pair and trained_pair != currency_pair:
        raise HTTPException(
            status_code=400,
            detail=f"Model is trained for {trained_pair}, not {currency_pair}",
        )

    cache_key = f"{currency_pair}_{req.days}_{req.amount}"
    cached = forecast_cache.get(cache_key)
    if cached and cached["expiry"] > datetime.now():
        return cached["data"]

    model = get_forecast_model()

    try:
        # Frankfurter supplies business-day FX observations, so don't invent
        # weekend market observations in the forecast horizon.
        future = model.make_future_dataframe(
            periods=req.days,
            include_history=False,
            freq="B",
        )
        forecast = model.predict(future)
        result_df = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()

        clean_result = []
        for _, row in result_df.iterrows():
            rate = max(float(row["yhat"]), 0.0)
            lower = max(float(row["yhat_lower"]), 0.0)
            upper = max(float(row["yhat_upper"]), 0.0)
            clean_result.append(
                {
                    "date": row["ds"].strftime("%Y-%m-%d"),
                    "rate": round(rate, 4),
                    "lower_bound": round(lower, 4),
                    "upper_bound": round(upper, 4),
                }
            )

        if not clean_result:
            raise RuntimeError("Forecast model returned no predictions")

        current_rate = clean_result[0]["rate"]
        best_match = max(clean_result, key=lambda item: item["rate"])
        expected_gain_per_unit = round(best_match["rate"] - current_rate, 4)
        expected_gain_total = round(expected_gain_per_unit * req.amount, 2)

        best_date = date.fromisoformat(best_match["date"])
        days_to_wait = max((best_date - date.today()).days, 0)

        if expected_gain_per_unit > 0.05 and days_to_wait > 0:
            recommendation = f"Wait {days_to_wait} days for better rate"
        else:
            recommendation = "Send now - rates are stable or declining"

        trend = (
            "increasing"
            if clean_result[-1]["rate"] > clean_result[0]["rate"]
            else "decreasing"
        )

        interval_width_pct = (
            (best_match["upper_bound"] - best_match["lower_bound"])
            / best_match["rate"]
            * 100
            if best_match["rate"] > 0
            else 100.0
        )
        confidence = (
            "High"
            if interval_width_pct <= 1
            else "Medium"
            if interval_width_pct <= 3
            else "Low"
        )

        final_response = {
            "pair": f"{from_curr}/{to_curr}",
            "amount": req.amount,
            "best_day": best_match["date"],
            "expected_rate": best_match["rate"],
            "expected_gain_per_unit": expected_gain_per_unit,
            "expected_gain_total": expected_gain_total,
            "recommendation": recommendation,
            "trend": trend,
            "confidence": confidence,
            "forecast_interval_width_percent": round(interval_width_pct, 2),
            "model_metrics": forecast_metadata.get("metrics", {}),
            "forecast": clean_result,
        }

        forecast_cache[cache_key] = {
            "data": final_response,
            "expiry": datetime.now() + timedelta(hours=1),
        }
        return final_response
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Forecasting error")
        raise HTTPException(status_code=500, detail="Forecasting failed") from exc


class Transaction(BaseModel):
    amount: float = Field(gt=0, le=10_000_000)
    frequency: float = Field(ge=0)
    route_id: int


def get_fraud_model():
    global fraud_model
    if fraud_model is None:
        model_path = FRAUD_MODEL_PATH if FRAUD_MODEL_PATH.exists() else LEGACY_FRAUD_MODEL_PATH
        if not model_path.exists():
            raise HTTPException(status_code=503, detail="Fraud model not found")
        try:
            fraud_model = joblib.load(model_path)
        except Exception as exc:
            logger.exception("Failed to load fraud model")
            raise HTTPException(status_code=503, detail="Fraud model could not be loaded") from exc
    return fraud_model


@app.post("/fraud-check")
async def fraud_check(transaction: Transaction):
    logger.info("Checking fraud for route %s", transaction.route_id)
    model = get_fraud_model()
    try:
        prediction = model.predict(
            [[transaction.amount, transaction.frequency, transaction.route_id]]
        )
        return {"isFraud": bool(prediction[0] == -1)}
    except Exception as exc:
        logger.exception("Fraud check error")
        raise HTTPException(status_code=500, detail="Fraud check failed") from exc


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting ML Service on http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info", reload=False)

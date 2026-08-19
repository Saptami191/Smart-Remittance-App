from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path

import joblib
import pandas as pd
from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SmartRemit ML Service")

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR.parent / "ml_model" / "forecast_model.joblib"
METADATA_PATH = BASE_DIR.parent / "ml_model" / "forecast_model_metadata.json"
FRAUD_MODEL_PATH = BASE_DIR.parent / "ml_model" / "fraud_model.pkl"
LEGACY_FRAUD_MODEL_PATH = BASE_DIR.parent / "fraud_model.pkl"

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
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        raise HTTPException(status_code=503, detail="Forecast model is not available")
    return {"status": "ready"}


@app.post("/predict-route")
async def predict_route(routes: list[Route]):
    if not routes:
        raise HTTPException(status_code=400, detail="No routes provided")
    df = pd.DataFrame([r.model_dump() for r in routes])
    df["score"] = df.apply(
        lambda row: score_route(
            row["fee"], row["exchange_rate"], row["time"], row["reliability"]
        ),
        axis=1,
    )
    return df.loc[df["score"].idxmax()].to_dict()


class ForecastRequest(BaseModel):
    from_curr: str = Field(default="USD", min_length=3, max_length=3)
    to_curr: str = Field(default="INR", min_length=3, max_length=3)
    amount: float = Field(default=1000.0, gt=0, le=10_000_000)
    days: int = Field(default=7, ge=1, le=30)


def get_forecast_model():
    global forecast_model, forecast_metadata
    if forecast_model is not None:
        return forecast_model

    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        raise HTTPException(status_code=503, detail="Forecast model is unavailable")

    try:
        forecast_model = joblib.load(MODEL_PATH)
        forecast_metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        if forecast_metadata.get("status") != "promoted":
            raise HTTPException(status_code=503, detail="No validated forecast model is promoted")
        logger.info("Loaded %s forecast model", forecast_metadata.get("model_type"))
        return forecast_model
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to load forecast model")
        raise HTTPException(status_code=503, detail="Forecast model could not be loaded") from exc


def forecast_candidate(model, model_type: str, days: int) -> list[dict]:
    if model_type == "prophet":
        future = model.make_future_dataframe(periods=days, include_history=False, freq="B")
        forecast = model.predict(future)
        return [
            {
                "date": row.ds.strftime("%Y-%m-%d"),
                "rate": round(max(float(row.yhat), 0.0), 4),
                "lower_bound": round(max(float(row.yhat_lower), 0.0), 4),
                "upper_bound": round(max(float(row.yhat_upper), 0.0), 4),
            }
            for row in forecast.itertuples()
        ]

    if model_type in {"naive", "moving_average_7", "exponential_smoothing"}:
        value = float(model["value"])
        today = date.today()
        return [
            {
                "date": (today + timedelta(days=offset)).isoformat(),
                "rate": round(max(value, 0.0), 4),
                "lower_bound": None,
                "upper_bound": None,
            }
            for offset in range(1, days + 1)
        ]

    raise ValueError(f"Unsupported forecast model type: {model_type}")


@app.post("/forecast")
async def forecast_rates(req: ForecastRequest = Body(...)):
    from_curr = req.from_curr.upper()
    to_curr = req.to_curr.upper()
    currency_pair = f"{from_curr}{to_curr}"

    model = get_forecast_model()
    trained_pair = "".join(
        [
            str(forecast_metadata.get("from_currency", "")),
            str(forecast_metadata.get("to_currency", "")),
        ]
    )
    if trained_pair and trained_pair != currency_pair:
        raise HTTPException(status_code=400, detail=f"Model is trained for {trained_pair}, not {currency_pair}")

    cache_key = f"{currency_pair}_{req.days}_{req.amount}"
    cached = forecast_cache.get(cache_key)
    if cached and cached["expiry"] > datetime.now():
        return cached["data"]

    try:
        model_type = forecast_metadata.get("model_type")
        clean_result = forecast_candidate(model, model_type, req.days)
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

        trend = "increasing" if clean_result[-1]["rate"] > clean_result[0]["rate"] else "stable"
        interval_width_pct = None
        bounds_available = [x for x in clean_result if x["lower_bound"] is not None and x["rate"] > 0]
        if bounds_available:
            widest = max(bounds_available, key=lambda item: item["rate"])
            interval_width_pct = (widest["upper_bound"] - widest["lower_bound"]) / widest["rate"] * 100

        confidence = None
        if interval_width_pct is not None:
            confidence = "High" if interval_width_pct <= 1 else "Medium" if interval_width_pct <= 3 else "Low"

        final_response = {
            "pair": f"{from_curr}/{to_curr}",
            "amount": req.amount,
            "model_type": model_type,
            "best_day": best_match["date"],
            "expected_rate": best_match["rate"],
            "expected_gain_per_unit": expected_gain_per_unit,
            "expected_gain_total": expected_gain_total,
            "recommendation": recommendation,
            "trend": trend,
            "confidence": confidence,
            "forecast_interval_width_percent": round(interval_width_pct, 2) if interval_width_pct is not None else None,
            "model_metrics": forecast_metadata.get("backtest", {}),
            "forecast": clean_result,
        }
        forecast_cache[cache_key] = {"data": final_response, "expiry": datetime.now() + timedelta(hours=1)}
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
    model = get_fraud_model()
    try:
        prediction = model.predict([[transaction.amount, transaction.frequency, transaction.route_id]])
        return {"isFraud": bool(prediction[0] == -1)}
    except Exception as exc:
        logger.exception("Fraud check error")
        raise HTTPException(status_code=500, detail="Fraud check failed") from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info", reload=False)

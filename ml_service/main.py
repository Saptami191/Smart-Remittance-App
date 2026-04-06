from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import joblib
from prophet import Prophet
import json
import os
import sys
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SmartRemit ML Service")

# --- DATA PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
MODEL_PATH = os.path.join(BASE_DIR, "..", "ml_model", "fraud_model.pkl")

# Cache for forecast
forecast_cache = {
    "data": None,
    "expiry": None
}

def score_route(fee, rate, time, reliability):
    return (rate * reliability) - (fee * 0.5) - (time / 1000)

class Route(BaseModel):
    id: int
    fee: float
    exchange_rate: float
    time: float
    reliability: float

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/predict-route")
async def predict_route(routes: list[Route]):
    logger.info(f"Predicting route for {len(routes)} options")
    if not routes:
        raise HTTPException(status_code=400, detail="No routes provided")
    
    df = pd.DataFrame([r.dict() for r in routes])
    df["score"] = df.apply(
        lambda row: score_route(row["fee"], row["exchange_rate"], row["time"], row["reliability"]),
        axis=1
    )
    best = df.loc[df["score"].idxmax()]
    return best.to_dict()

class ForecastRequest(BaseModel):
    from_curr: str = "USD"
    to_curr: str = "INR"
    amount: float = 1000.0
    days: int = 7

@app.post("/forecast")
async def forecast_rates(req: ForecastRequest = Body(...)):
    global forecast_cache
    
    currency_pair = f"{req.from_curr}{req.to_curr}"
    cache_key = f"{currency_pair}_{req.days}_{req.amount}"
    
    if forecast_cache.get(cache_key) and forecast_cache[cache_key]["expiry"] > datetime.now():
        logger.info(f"Returning cached forecast for {cache_key}")
        return forecast_cache[cache_key]["data"]

    logger.info(f"Training new forecast model for {currency_pair}...")
    csv_path = os.path.join(DATA_DIR, "forex_rates.csv")
    if not os.path.exists(csv_path):
        logger.error(f"Data file not found at {csv_path}")
        raise HTTPException(status_code=404, detail="Forex rates data not found")
    
    try:
        df = pd.read_csv(csv_path)
        df = df.rename(columns={'date': 'ds', 'exchange_rate': 'y'})
        
        model = Prophet(daily_seasonality=True, interval_width=0.95)
        model.fit(df)
        
        future = model.make_future_dataframe(periods=req.days)
        forecast = model.predict(future)
        
        result_df = forecast[['ds', 'yhat']].tail(req.days)
        result_df['date'] = result_df['ds'].dt.strftime('%Y-%m-%d')
        
        clean_result = [
            {"date": row['date'], "rate": round(row['yhat'], 2)}
            for _, row in result_df.iterrows()
        ]
        
        # --- SMART INSIGHTS & RECOMMENDATION ---
        current_rate = clean_result[0]["rate"]
        best_match = max(clean_result, key=lambda x: x["rate"])
        
        # Gain per unit (e.g. per 1 USD)
        expected_gain_per_unit = round(best_match["rate"] - current_rate, 2)
        
        # Total gain for the requested amount
        expected_gain_total = round(expected_gain_per_unit * req.amount, 2)
        
        days_to_wait = (datetime.strptime(best_match["date"], '%Y-%m-%d') - datetime.now()).days + 1
        
        if expected_gain_per_unit > 0.05:
            recommendation = f"Wait {days_to_wait} days for better rate" if days_to_wait > 0 else "Send now for maximum value"
        else:
            recommendation = "Send now - rates are stable or declining"

        trend = "increasing" if clean_result[-1]["rate"] > clean_result[0]["rate"] else "decreasing"
        
        # Simple confidence logic based on forecast horizon
        confidence = "High" if req.days <= 3 else "Medium"

        final_response = {
            "pair": f"{req.from_curr}/{req.to_curr}",
            "amount": req.amount,
            "best_day": best_match["date"],
            "expected_rate": best_match["rate"],
            "expected_gain_per_unit": expected_gain_per_unit,
            "expected_gain_total": expected_gain_total,
            "recommendation": recommendation,
            "trend": trend,
            "confidence": confidence,
            "forecast": clean_result
        }
            
        forecast_cache[cache_key] = {
            "data": final_response,
            "expiry": datetime.now() + timedelta(hours=1)
        }
        
        return final_response
    except Exception as e:
        logger.error(f"Forecasting error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Forecasting failed: {str(e)}")

class Transaction(BaseModel):
    amount: float
    frequency: float
    route_id: int

@app.post("/fraud-check")
async def fraud_check(transaction: Transaction):
    logger.info(f"Checking fraud for transaction: {transaction}")
    model_to_use = MODEL_PATH
    if not os.path.exists(model_to_use):
        model_to_use = os.path.join(BASE_DIR, "..", "fraud_model.pkl")
        
    if not os.path.exists(model_to_use):
        logger.error("Fraud model file not found")
        raise HTTPException(status_code=404, detail="Fraud model not found")
    
    try:
        model = joblib.load(model_to_use)
        prediction = model.predict([[transaction.amount, transaction.frequency, transaction.route_id]])
        return {"isFraud": bool(prediction[0] == -1)}
    except Exception as e:
        logger.error(f"Fraud check error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fraud check failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import time
    logger.info("🚀 Starting ML Service on http://127.0.0.1:8000")
    try:
        # Using 127.0.0.1 explicitly for Windows stability
        uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info", reload=False)
    except Exception as e:
        logger.error(f"❌ ML Service failed: {e}")
        time.sleep(10) # Keep terminal open so user can see error

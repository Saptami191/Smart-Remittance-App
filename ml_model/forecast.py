# import pandas as pd
# from prophet import Prophet
# import json

# def train_forecast_model(csv_path):
#     df = pd.read_csv(csv_path)
#     df = df.rename(columns={'date': 'ds', 'exchange_rate': 'y'})
#     model = Prophet()
#     model.fit(df)
#     return model

# def predict_next_rate(model, days=7):
#     future = model.make_future_dataframe(periods=days)
#     forecast = model.predict(future)
#     return forecast[['ds', 'yhat']].tail(days)

# if __name__ == "__main__":
#     model = train_forecast_model("data/forex_rates.csv")
#     forecast = predict_next_rate(model)
#     print(forecast.to_json(orient='records'))
    
#     model = train_forecast_model("../data/forex_rates.csv")



import pandas as pd
from prophet import Prophet
import json

def train_forecast_model(csv_path):
    df = pd.read_csv(csv_path)
    df = df.rename(columns={'date': 'ds', 'exchange_rate': 'y'})
    model = Prophet()
    model.fit(df)
    return model

def predict_next_rate(model, days=7):
    future = model.make_future_dataframe(periods=days)
    forecast = model.predict(future)
    return forecast[['ds', 'yhat']].tail(days)

if __name__ == "__main__":
    # ✅ Use correct path (go up from ml_model/ to find data/)
    model = train_forecast_model("../data/forex_rates.csv")
    forecast = predict_next_rate(model)
    print(forecast.to_json(orient='records'))

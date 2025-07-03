import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
import sys
import json

def train_fraud_model(data_csv):
    df = pd.read_csv(data_csv)
    model = IsolationForest(contamination=0.01)
    model.fit(df[['amount', 'frequency', 'route_id']])
    joblib.dump(model, 'fraud_model.pkl')

if __name__ == '__main__':
    input_data = json.loads(sys.argv[1])
    model = joblib.load('fraud_model.pkl')
    prediction = model.predict([input_data])
    print(prediction[0] == -1)

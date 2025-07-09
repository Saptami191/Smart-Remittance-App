import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

def train_fraud_model(csv_path):
    # Load transaction data
    df = pd.read_csv(csv_path)

    # Train Isolation Forest on selected features
    model = IsolationForest(contamination=0.01, random_state=42)
    model.fit(df[['amount', 'frequency', 'route_id']])

    # Save the trained model
    joblib.dump(model, 'fraud_model.pkl')
    print("✅ fraud_model.pkl saved successfully.")

# Train the model with a sample CSV
if __name__ == '__main__':
    train_fraud_model('../data/transactions.csv')

import pandas as pd
import sys
import json

def score_route(fee, rate, time, reliability):
    return (rate * reliability) - (fee * 0.5) - (time / 1000)

def best_route(routes_df):
    routes_df["score"] = routes_df.apply(
        lambda row: score_route(row["fee"], row["exchange_rate"], row["time"], row["reliability"]),
        axis=1
    )
    return routes_df.loc[routes_df["score"].idxmax()]

if __name__ == "__main__":
    input_text = sys.stdin.read()
    input_data = json.loads(input_text)
    df = pd.DataFrame(input_data)
    best = best_route(df)
    print(best.to_json())

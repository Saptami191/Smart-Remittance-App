import json
import os

DB = "data/users.json"

def update_progress(user, topic, score, total):
    if not os.path.exists(DB):
        data = {}
    else:
        with open(DB) as f:
            data = json.load(f)

    if user not in data:
        data[user] = {}

    data[user][topic] = {"score": score, "total": total}

    with open(DB, "w") as f:
        json.dump(data, f, indent=2)

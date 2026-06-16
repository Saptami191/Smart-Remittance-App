# import json

# def recommend_next_topic(user):
#     with open("data/users.json") as f:
#         data = json.load(f)

#     topics = data.get(user, {})
#     weak_topics = [k for k, v in topics.items() if v["score"] / v["total"] < 0.6]

#     if weak_topics:
#         return f"📌 Focus more on: {', '.join(weak_topics)}"
#     return "🎉 You're doing great! Try new topics."


import json

def recommend_next_topic(username):
    with open("data/users.json", "r") as f:
        data = json.load(f)

    user_data = data.get(username)

    if not user_data:
        return "No data found for this user."

    progress = user_data.get("progress", {})

    # Recommend the topic with lowest progress
    next_topic = min(progress, key=progress.get, default=None)

    if next_topic:
        return f"Next topic to study: {next_topic} ({progress[next_topic]}% complete)"
    else:
        return "You're all caught up! 🎉"

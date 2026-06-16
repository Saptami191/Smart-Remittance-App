from quiz import run_quiz
from tracker import update_progress
from recommender import recommend_next_topic
from qa_bot import ask_ai  # optional

def main():
    user = input("👤 Enter your name: ")
    while True:
        print("\n📘 Menu")
        print("1. Take Quiz")
        print("2. View Recommendation")
        print("3. Ask AI (optional)")
        print("4. Exit")
        choice = input("Choose an option: ")

        if choice == '1':
            topic = input("Enter topic (Python/Math): ")
            score, total = run_quiz(topic)
            print(f"✅ Score: {score}/{total}")
            update_progress(user, topic, score, total)

        elif choice == '2':
            print(recommend_next_topic(user))

        elif choice == '3':
            q = input("Ask me anything: ")
            print("🤖 AI says:", ask_ai(q))

        else:
            break

if __name__ == "__main__":
    main()

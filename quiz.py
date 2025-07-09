quiz_data = {
    "Python": {
        "What is a list comprehension?": "A concise way to create lists.",
        "What does 'len()' do?": "Returns length of a sequence."
    },
    "Math": {
        "What is 2 + 2?": "4",
        "What is the derivative of x^2?": "2x"
    }
}

def run_quiz(topic):
    correct = 0
    total = len(quiz_data.get(topic, {}))
    for question, answer in quiz_data.get(topic, {}).items():
        print("\n" + question)
        user_answer = input("Your answer: ").strip()
        if user_answer.lower() == answer.lower():
            correct += 1
    return correct, total

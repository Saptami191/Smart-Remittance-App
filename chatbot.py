



# -*- coding: utf-8 -*-

from textblob import TextBlob
import json
import nltk
from nltk.stem import RSLPStemmer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize import WordPunctTokenizer
import numpy as np

# Download necessary NLTK tools
nltk.download('rslp')
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')  # Added to fix punkt_tab error
nltk.download('averaged_perceptron_tagger')

# Initialize tokenizer, stemmer, and stopwords
tokenizer = WordPunctTokenizer()
stemmer = RSLPStemmer()
stop_words = set(stopwords.words('portuguese'))

# Text preprocessing function
def preprocess_text(text):
    text = text.lower()
    tokens = tokenizer.tokenize(text)
    tokens = [word for word in tokens if word not in stop_words]
    stemmed = [stemmer.stem(word) for word in tokens]
    return ' '.join(stemmed)

# Load previous conversation data
try:
    with open('conversations.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
except FileNotFoundError:
    data = []

# Initialize vectorizer and model
vectorizer = TfidfVectorizer()
model = KMeans(n_clusters=2)

# Build question-answer pairs
conversations = []
for item in data:
    # Handle both old and new JSON formats
    if 'conversation' in item:
        question, answer = item['conversation'].split(';')
        conversations.append({'question': question.strip(), 'answer': answer.strip()})
    else:
        conversations.append({
            'question': item.get('question', ''),
            'answer': item.get('answer', ''),
            'cluster': item.get('cluster', 0)
        })

# Vectorize all questions if there are any
if conversations:
    questions = [c['question'] for c in conversations]
    X = vectorizer.fit_transform(questions)
    # Train the model
    model.fit(X)
else:
    questions = []
    X = None

# Function to get intent (cluster)
def get_intent(question):
    if not questions:  # Handle empty conversations
        return 0
    x = vectorizer.transform([question])
    return int(model.predict(x)[0])  # Convert to int

# Add cluster label to each conversation
for i, c in enumerate(conversations):
    if X is not None:
        x = vectorizer.transform([c['question']])
        conversations[i]['cluster'] = int(model.predict(x)[0])  # Convert to int
    else:
        conversations[i]['cluster'] = 0

# Input from user
original_question = input('User: ')
processed_question = preprocess_text(original_question)

# Identify cluster
cluster = get_intent(processed_question)

# Get related conversations
related = [c for c in conversations if c['cluster'] == cluster]

# Find best match using cosine similarity
answer = 'Sorry, I didn\'t understand your question.'
if related and X is not None:
    processed_questions = [preprocess_text(c['question']) for c in related]
    question_vectors = vectorizer.transform(processed_questions)
    input_vector = vectorizer.transform([processed_question])
    similarities = cosine_similarity(input_vector, question_vectors)[0]
    best_match_idx = np.argmax(similarities)
    if similarities[best_match_idx] > 0:  # Threshold for similarity
        answer = related[best_match_idx]['answer']

# If no match, try keyword-based fallback
if answer == 'Sorry, I didn\'t understand your question.':
    def handle_unknown(question):
        tokens = tokenizer.tokenize(question.lower())
        tagged = nltk.pos_tag(tokens)
        keywords = [word for word, pos in tagged if pos.startswith('NN') or pos.startswith('VB')]
        related = [c for c in conversations if any(k.lower() in c['question'].lower() for k in keywords)]
        if related:
            processed_questions = [preprocess_text(c['question']) for c in related]
            if processed_questions and X is not None:
                question_vectors = vectorizer.transform(processed_questions)
                input_vector = vectorizer.transform([processed_question])
                similarities = cosine_similarity(input_vector, question_vectors)[0]
                best_match_idx = np.argmax(similarities)
                return related[best_match_idx]['answer']
        return 'Sorry, I didn\'t understand your question.'
    
    answer = handle_unknown(original_question)

# Respond
print('Answer:', answer)

# Save new Q&A
conversations.append({
    'question': original_question,
    'answer': answer,
    'cluster': get_intent(preprocess_text(original_question))
})

# Save to JSON
with open('conversations.json', 'w', encoding='utf-8') as file:
    json.dump(conversations, file, indent=4, ensure_ascii=False)
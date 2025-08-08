💱 SmartRemit — AI-Powered Remittance Route Optimizer
🌍 Overview
SmartRemit is an AI-driven remittance optimization platform designed for emerging markets.
It helps users send money faster, cheaper, and more securely by selecting the best remittance route in real-time.

The platform combines:

Dynamic route optimization

Currency rate forecasting

Fraud detection

NLP-powered customer assistance

This ensures maximum savings for senders and efficient delivery for receivers.

🚀 Key Features
🔹 Real-Time Remittance Route Optimization
Uses Random Forest ML models to determine the cheapest & fastest transfer route.

Considers exchange rates, fees, transfer time, and reliability.

🔹 Currency Rate Forecasting
Built with Facebook Prophet to predict near-future currency fluctuations.

Helps users choose the right time to send money.

🔹 Fraud Detection
AI model flags suspicious transfers to protect users from scams and laundering activities.

🔹 Multilingual NLP Assistance
Chatbot for 24/7 customer queries in multiple languages.

Uses AI for natural, human-like interactions.

🛠️ Tech Stack
Component	Technology
Frontend	HTML, CSS, JavaScript
Backend	Node.js, Express.js
Database	MongoDB
Machine Learning	Python (Scikit-learn, Prophet, Pandas, NumPy)
Integration	REST APIs
Deployment	Render / Vercel / Railway

📂 Project Structure
graphql
Copy
Edit
SmartRemit/
│
├── backend/         # Node.js API for frontend & ML model connection
├── ml-models/       # ML scripts for route prediction & rate forecasting
├── frontend/        # Web UI files
├── dataset/         # Training datasets
└── README.md
⚙️ Installation & Setup
1️⃣ Clone the Repository
bash
Copy
Edit
git clone [(https://github.com/Saptami191/Smart-Remit.git]
cd SmartRemit
2️⃣ Install Backend Dependencies
bash
Copy
Edit
cd backend
npm install
3️⃣ Install ML Model Dependencies
bash
Copy
Edit
cd ../ml-models
pip install -r requirements.txt
4️⃣ Start Backend
bash
Copy
Edit
cd ../backend
node server.js
5️⃣ Run ML Model API
bash
Copy
Edit
cd ../ml-models
python app.py
6️⃣ Open Frontend in Browser
pgsql
Copy
Edit
Open frontend/index.html
📊 AI Model Details
Remittance Route Classifier:

Model: Random Forest

Input: Exchange rate, fees, transfer time, reliability score

Output: Best remittance provider

Currency Rate Forecaster:

Model: Facebook Prophet

Input: Historical currency rates

Output: Predicted rates for next 7 days

🌟 Impact
Financial Inclusion: Empowers users in rural & developing regions.

Cost Savings: Helps people save up to 15% per transaction.

Security: AI-driven fraud prevention keeps users safe.

👥 Team
[Saptami Biswas] – Backend & ML Integration

[Aradhya Dwivedi] – Frontend Development

[Bikram Sadhukhan] – Data Collection & Model Training

[Debdwaipayan Halder] - Backend  

📜 License
This project is licensed under the MIT License.





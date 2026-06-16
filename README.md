# 💱 SmartRemit — AI-Powered Remittance Optimizer

## 🌍 Overview

SmartRemit is a full-stack fintech application that helps users decide the **best time to send money internationally** using AI-driven currency forecasting and optimization.

It provides actionable recommendations like:
👉 *Send now* or *Wait for better rate*
along with **expected monetary gain**

---

## 🚀 Live Demo

* 🌐 Frontend: https://smart-remittance-app.vercel.app
* ⚙️ Backend API: https://smart-remittance-app-1.onrender.com

---

## ⚙️ Features

### 📈 Currency Forecasting
* Predicts short-term exchange rate trends using **Prophet**

### 💡 Smart Recommendations
* Suggests optimal timing for remittance
* Calculates expected savings based on user amount

### 🔐 Authentication
* JWT-based login/signup
* Secure password hashing (bcrypt)

### 📊 Interactive Dashboard
* Visual charts for currency trends
* Dynamic updates based on user input

---

## 🛠️ Tech Stack

| Layer      | Technology                     |
| ---------- | ------------------------------ |
| Frontend   | HTML, CSS, JavaScript          |
| Backend    | Node.js, Express               |
| Database   | MongoDB Atlas                  |
| ML         | Python (Prophet, Scikit-learn) |
| Deployment | Vercel + Render                |

---

## 🏗️ Architecture

Frontend (Vercel)
→ Backend API (Render)
→ MongoDB Atlas
→ ML Service (Python - local / in progress)

---

## 📂 Project Structure

```id="srm6pa"
Smart-Remittance-App/
│
├── backend/        # Express API
├── ml_service/     # Python ML models
├── frontend/       # UI files
└── README.md
```

---

## ⚠️ Current Limitations

* ML service is **not fully deployed yet**
* Some endpoints may not work in production
* Focus is on core recommendation system

---

## 🤝 Contributing

Contributions are welcome!

### Areas where help is needed:
* 🚀 Deploy ML service (Python API)
* 🎨 Improve frontend UI/UX
* ⚙️ API error handling & optimization

### Steps to contribute:
1. Fork the repository
2. Create a new branch
3. Make changes
4. Submit a Pull Request

---

## 🧪 Local Setup

```bash id="1q4c6g"
git clone https://github.com/Saptami191/Smart-Remittance-App.git
cd Smart-Remittance-App
```

### Backend

```bash id="5lmt4z"
cd backend
npm install
node app.js
```

### ML Service

```bash id="v2n1jk"
cd ../ml_service
pip install -r requirements.txt
python main.py
```

### Frontend

Open `index.html` or `dashboard.html` in browser

---

## 🎯 Key Highlights

* End-to-end full-stack system
* Real-world fintech use case
* Personalized financial insights
* Live deployed backend + frontend

---

## 👩💻 Author



---

## 📜 License

MIT License

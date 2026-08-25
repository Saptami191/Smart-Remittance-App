# 💱 SmartRemit

### AI-powered remittance timing, FX intelligence, and decision support

[![Node.js](https://img.shields.io/badge/Node.js-20%2B-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/atlas)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**SmartRemit** is a full-stack fintech application that helps users make a better decision about **when to send an international money transfer**.

Instead of simply displaying an exchange rate, SmartRemit combines historical FX data, forecasting, rolling backtesting, model selection, and recommendation logic to answer a practical question:

> **Should I send the money now, or is waiting likely to give me a better outcome?**

---

## 🚀 Live Project

| Resource | Link |
|---|---|
| 🌐 **Live Frontend** | [Open SmartRemit](https://smart-remittance-app.vercel.app) |
| ⚙️ **Production API** | [smartremit-api.onrender.com](https://smartremit-api.onrender.com) |
| 🤖 **ML Service** | [smartremit-ml.onrender.com](https://smartremit-ml.onrender.com) |
| 💻 **GitHub Repository** | [Saptami191/Smart-Remittance-App](https://github.com/Saptami191/Smart-Remittance-App) |

> **Deployment note:** the application is actively being stabilized for production. The API, ML service, authentication, and cloud deployment are being tested independently before the final public demo is considered production-ready.

---

## 🎯 The Problem

International remittance users face a simple but important decision:

**Send money now or wait for a potentially better exchange rate?**

Most remittance interfaces provide the current rate but do not help users reason about short-term FX movement or quantify what waiting could mean for the amount they want to send.

SmartRemit turns that uncertainty into a data-driven decision-support workflow.

```text
Remittance Amount
       ↓
Current FX Rate
       ↓
Historical FX Intelligence
       ↓
Multiple Forecasting Candidates
       ↓
Rolling Backtesting
       ↓
Best Validated Model
       ↓
Expected Gain / Loss
       ↓
Send Now / Wait Recommendation
```

---

## ✨ What SmartRemit Does

- 📈 Tracks and analyses historical exchange-rate behaviour
- 🤖 Evaluates multiple forecasting strategies
- 🧪 Uses rolling backtesting instead of blindly trusting one model
- 🎯 Selects a forecasting candidate based on recent validation performance
- 💰 Estimates potential gain for a user-defined remittance amount
- 💡 Generates an actionable **Send Now / Wait** recommendation
- 📊 Provides an exchange-rate intelligence dashboard
- 🔐 Uses JWT authentication and bcrypt password hashing
- 🗄️ Stores users and remittance history in MongoDB Atlas
- ☁️ Separates the API and ML workloads for cloud deployment

---

## 🧠 AI / ML: Model Selection, Not Model Worship

A core engineering principle in SmartRemit is:

> **A complex model should not win just because it is complex.**

The forecasting pipeline compares multiple candidates:

| Candidate | Role |
|---|---|
| Naive | Recent-rate baseline |
| Moving Average (7) | Short-term smoothing |
| Exponential Smoothing | Recency-weighted trend |
| Prophet | Time-series forecasting |

Candidates are evaluated using rolling validation with:

- **MAE** — Mean Absolute Error
- **RMSE** — Root Mean Squared Error
- **MAPE** — Mean Absolute Percentage Error
- Comparison against a naive baseline

The best-performing candidate can be promoted as the production forecasting artifact.

This prevents the system from assuming that Prophet, or any other sophisticated model, will automatically outperform a simple baseline.

### Example validation result

A recent training run evaluated four candidates over rolling 30-observation validation windows:

```text
naive                  1.121667
moving_average_7       1.047762  ← selected
exponential_smoothing  1.081665
prophet                1.299733
```

The important part is the **validation and promotion process**, not the absolute score. SmartRemit uses evidence from recent historical data before selecting the production candidate.

---

## 🏗️ Architecture

```text
                         ┌───────────────────────┐
                         │       Vercel          │
                         │   Frontend / Static   │
                         └───────────┬───────────┘
                                     │ HTTPS
                                     ▼
                         ┌───────────────────────┐
                         │        Render         │
                         │     Node / Express    │
                         │       API Service     │
                         └───────┬───────┬───────┘
                                 │       │
                      ┌──────────┘       └──────────┐
                      ▼                             ▼
             ┌─────────────────┐           ┌─────────────────┐
             │  MongoDB Atlas  │           │   Render ML     │
             │ Users / History │           │ Python / FastAPI│
             └─────────────────┘           └────────┬────────┘
                                                     │
                                                     ▼
                                          ┌────────────────────┐
                                          │ Forecasting +      │
                                          │ Backtesting +      │
                                          │ Model Selection    │
                                          └────────────────────┘
```

### Service separation

**Frontend**
- Static HTML/CSS/JavaScript
- Hosted on Vercel

**API service**
- Node.js + Express
- Authentication
- Protected application APIs
- MongoDB integration
- Hosted on Render

**ML service**
- Python + FastAPI
- FX forecasting
- Model evaluation and selection
- Hosted separately on Render

This separation keeps model-serving workloads independent from the application API and makes each component easier to deploy and scale.

---

## 🔐 Authentication & API

Authentication uses:

- JWT access tokens
- bcrypt password hashing
- Protected API routes
- MongoDB-backed user accounts

### Public endpoints

```http
POST /api/signup
POST /api/login
```

### Protected endpoints

```http
POST /api/route
GET  /api/forecast
POST /api/fraud
GET  /api/history
```

Protected endpoints require a valid JWT in the request authorization header.

Example:

```http
Authorization: Bearer <JWT_TOKEN>
```

**Passwords are never intended to be stored as plaintext.** Secrets such as `MONGO_URI` and `JWT_SECRET` must remain in deployment environment variables.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Node.js, Express |
| Authentication | JWT, bcrypt |
| Database | MongoDB Atlas, Mongoose |
| ML / Forecasting | Python, FastAPI, Prophet, Scikit-learn |
| Evaluation | Rolling backtesting, MAE, RMSE, MAPE |
| Deployment | Vercel + Render |
| CI/CD | GitHub Actions |
| Source Control | Git + GitHub |

---

## 📂 Repository Structure

```text
Smart-Remittance-App/
│
├── backend/
│   ├── controllers/          # Authentication and application logic
│   ├── middleware/           # JWT authentication middleware
│   ├── models/               # MongoDB/Mongoose models
│   ├── routes/               # API routes
│   ├── app.js / server.js    # Node backend entry points
│   └── package.json
│
├── ml_service/
│   ├── main.py               # ML API entry point
│   ├── train_forecast.py     # Training + model selection
│   ├── ingest_fx_data.py     # FX data ingestion
│   ├── test_forecast_service.py
│   └── requirements.txt
│
├── ml_model/                 # Promoted model artifacts
├── index2.html               # Authentication UI
├── dashboard.html            # Main application dashboard
├── style2.css                # Authentication styling
├── vercel.json               # Frontend/API deployment configuration
├── render.yaml               # Render Blueprint configuration
├── requirements.txt          # Root-level compatibility requirements
└── README.md
```

---

## 🚀 Run Locally

### Prerequisites

- Node.js 20+
- Python 3.10+
- MongoDB Atlas account or local MongoDB
- Git

### 1. Clone the repository

```bash
git clone https://github.com/Saptami191/Smart-Remittance-App.git
cd Smart-Remittance-App
```

### 2. Configure backend environment variables

Create `backend/.env`:

```env
MONGO_URI=your_mongodb_connection_string
JWT_SECRET=your_long_random_secret
ML_SERVICE_URL=http://localhost:8000
```

**Never commit this file.**

### 3. Start the Node API

```bash
cd backend
npm install
npm start
```

### 4. Start the ML service

In a second terminal:

```bash
cd ml_service
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 5. Train the forecasting pipeline

```bash
python train_forecast.py
```

### 6. Open the frontend

Serve the repository with a local static server rather than relying on `file://` URLs when testing API calls.

For example, with Python:

```bash
python -m http.server 5500
```

Then open:

```text
http://localhost:5500/index2.html
```

---

## 🧪 Testing

Run the forecasting service tests with:

```bash
pytest -q ml_service/test_forecast_service.py
```

The project also uses CI validation around the forecasting pipeline so model changes can be evaluated before promotion.

---

## ☁️ Deployment

The repository includes a Render Blueprint with separate services for the Node API and Python ML service.

### API service

```text
Runtime: Node
Root Directory: backend
Build: npm install
Start: npm start
```

### ML service

```text
Runtime: Python
Root Directory: ml_service
Build: pip install -r requirements.txt
Start: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Required API environment variables

```text
MONGO_URI
JWT_SECRET
ML_SERVICE_URL
```

### Required security practice

Do **not** commit:

- MongoDB passwords
- JWT secrets
- API keys
- `.env` files
- private deployment credentials

---

## 🧱 Engineering Decisions

### Why backtesting?

A forecasting model can look impressive while performing poorly on unseen data. SmartRemit therefore evaluates candidates using rolling historical validation rather than trusting training accuracy.

### Why compare against a naive baseline?

If a sophisticated model cannot reliably beat a simple baseline, there is little engineering justification for deploying the sophisticated model.

### Why separate API and ML services?

The API handles authentication, user data, business logic, and request routing. The ML service handles forecasting and model inference. Separating them reduces coupling and makes deployment and scaling more manageable.

### Why JWT + bcrypt?

The application needs stateless authentication for protected APIs while avoiding plaintext password storage. JWT handles authenticated requests; bcrypt handles password hashing.

---

## 🗺️ Roadmap

### Current

- [x] Full-stack application structure
- [x] Node/Express backend
- [x] MongoDB integration
- [x] JWT authentication architecture
- [x] bcrypt password hashing
- [x] FX forecasting pipeline
- [x] Rolling backtesting
- [x] Baseline comparison
- [x] Automatic candidate selection
- [x] Promoted model artifact
- [x] Render Blueprint configuration
- [x] Vercel frontend deployment

### Next

- [ ] Finish end-to-end production authentication verification
- [ ] Complete ML/API production integration testing
- [ ] Improve recommendation calibration
- [ ] Add stronger API failure recovery
- [ ] Add observability and structured logging
- [ ] Load-test the application
- [ ] Add real-time FX data refresh
- [ ] Expand remittance corridor coverage
- [ ] Add explainable recommendation summaries

---

## 🏆 Buildathon Positioning

SmartRemit is designed as a **proof-of-work fintech/AI system**, not an LLM wrapper.

The strongest technical story is the combination of:

```text
Real financial decision problem
          ↓
Historical FX data
          ↓
Multiple forecasting candidates
          ↓
Rolling validation
          ↓
Evidence-based model selection
          ↓
Expected financial impact
          ↓
Actionable recommendation
```

For an AI/finance evaluation, the project demonstrates that AI/ML is being used where it has a concrete job: **forecasting uncertain FX behaviour and supporting a financial decision**.

The next major evolution is to add agentic workflows around routing, compliance, explanation, and failure recovery without turning the product into an unnecessary LLM wrapper.

---

## 👩‍💻 Author

**Saptami Biswas**  
B.Tech Electrical Engineering · NIT Agartala

- GitHub: [@Saptami191](https://github.com/Saptami191)
- Repository: [Smart-Remittance-App](https://github.com/Saptami191/Smart-Remittance-App)

---

## 📜 License

This project is released under the **MIT License**.

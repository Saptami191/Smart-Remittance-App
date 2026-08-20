# 💱 SmartRemit

### AI-assisted remittance timing & exchange-rate intelligence

SmartRemit is a full-stack fintech application designed to help people make a better decision about **when to send an international money transfer**.

Instead of showing an exchange rate and leaving the user to guess, SmartRemit combines historical FX data, forecasting models, backtesting, and recommendation logic to answer a practical question:

> **Should I send the money now, or wait?**

---

## ✨ What SmartRemit Does

- 📈 Tracks historical exchange-rate behaviour
- 🤖 Evaluates multiple forecasting strategies
- 🧪 Uses rolling backtests instead of blindly trusting one ML model
- 🎯 Selects the candidate that performs best on recent validation data
- 💰 Estimates the potential gain for a remittance amount
- 💡 Produces an actionable **Send Now / Wait** recommendation
- 📊 Displays exchange-rate trends in a dashboard
- 🔐 Provides JWT authentication and bcrypt password hashing
- ☁️ Supports cloud deployment with Render and Vercel

---

## 🧠 Model Selection, Not Model Worship

A major design decision in SmartRemit is that **Prophet is not automatically promoted just because it is an ML model**.

The training pipeline currently compares:

| Candidate | Purpose |
|---|---|
| Naive | Recent-rate baseline |
| Moving Average (7) | Short-term smoothing |
| Exponential Smoothing | Recency-weighted trend |
| Prophet | Time-series forecasting |

Models are evaluated using rolling 30-observation backtests with metrics including:

- MAE
- RMSE
- MAPE
- Comparison against the naive baseline

The candidate with the strongest validation performance can be promoted as the production forecasting artifact.

This matters because a more sophisticated model is **not automatically a better model**. In the latest backtest, the 7-day moving average outperformed Prophet on mean MAE, so the pipeline promoted `moving_average_7` rather than forcing Prophet into production.

---

## 🏗️ Architecture

```text
                    ┌──────────────────────┐
                    │      Frontend        │
                    │ HTML / CSS / JS      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     Node / Express    │
                    │      Backend API      │
                    └───────┬───────┬──────┘
                            │       │
                  ┌─────────┘       └──────────┐
                  ▼                            ▼
        ┌──────────────────┐          ┌─────────────────┐
        │   MongoDB Atlas  │          │   ML Service    │
        │ Users / History  │          │ Python          │
        └──────────────────┘          └────────┬────────┘
                                               │
                                               ▼
                                    ┌────────────────────┐
                                    │ Forecast / Model   │
                                    │ Selection Pipeline │
                                    └────────────────────┘
```

### Production direction

```text
Vercel / Static Frontend
          ↓
Render API
          ↓
MongoDB Atlas
          ↓
Render ML Service
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Node.js, Express |
| Authentication | JWT, bcrypt |
| Database | MongoDB Atlas |
| ML / Forecasting | Python, Prophet, Scikit-learn |
| Validation | Rolling backtesting, MAE, RMSE, MAPE |
| CI/CD | GitHub Actions |
| Deployment | Vercel + Render |
| Source Control | Git + GitHub |

---

## 📂 Repository Structure

```text
Smart-Remittance-App/
│
├── backend/                  # Node.js / Express API
│   ├── routes/               # API routes
│   ├── models/               # Database models
│   └── app.js                # Backend entry point
│
├── ml_service/               # Python forecasting service
│   ├── train_forecast.py     # Training + model selection
│   ├── main.py               # ML API entry point
│   ├── test_forecast_service.py
│   └── requirements.txt
│
├── frontend/                 # Frontend application
│
├── ml_model/                 # Promoted model artifacts
│
├── .github/workflows/        # CI/CD workflows
│
├── render.yaml               # Render Blueprint configuration
└── README.md
```

---

## 🚀 Run Locally

### 1. Clone

```bash
git clone https://github.com/Saptami191/Smart-Remittance-App.git
cd Smart-Remittance-App
```

### 2. Backend

```bash
cd backend
npm install
npm start
```

Set the required environment variables before starting the backend, including your MongoDB connection string.

### 3. ML Service

```bash
cd ../ml_service
pip install -r requirements.txt
python main.py
```

To train and evaluate the forecasting pipeline:

```bash
python train_forecast.py
```

### 4. Frontend

For a simple static preview, open the frontend entry HTML file in a browser.

For development, serve the frontend through a local static server so API requests behave correctly.

---

## 🧪 Testing

The forecasting service includes tests covering promoted model artifacts and serving behaviour.

Run:

```bash
pytest -q ml_service/test_forecast_service.py
```

The CI pipeline also trains and validates the forecasting candidate before allowing the model artifact to be promoted.

---

## 📊 Example Training Result

A recent training run used **2,057 observations** from January 2021 through August 2026.

The rolling backtest evaluated four 30-observation folds and compared four candidates. The resulting mean MAE was approximately:

```text
naive                1.121667
moving_average_7     1.047762  ← selected
exponential_smoothing 1.081665
prophet              1.299733
```

The important point is not the absolute number; it is the validation process. SmartRemit refuses to promote a forecasting candidate when it fails to beat the naive baseline under the configured promotion rule.

---

## 🔐 Security

SmartRemit uses:

- JWT-based authentication
- bcrypt password hashing
- Protected API routes
- Environment variables for secrets
- MongoDB Atlas for managed database infrastructure

**Never commit `.env` files, database credentials, JWT secrets, or API keys to Git.**

---

## ☁️ Deployment

The repository includes a Render Blueprint for deploying separate services for the API and ML components.

Before production deployment, configure:

- `MONGO_URI`
- JWT secret
- ML service URL
- Any required frontend/API environment variables

The frontend and backend should be tested against their deployed URLs before considering the production setup complete.

---

## ⚠️ Current Status

SmartRemit is actively being developed.

### Working

- Full-stack application structure
- Authentication flow
- MongoDB integration
- FX forecasting pipeline
- Rolling backtesting
- Baseline comparison
- Automatic candidate selection
- Promoted model artifact
- Automated CI validation
- Frontend redesign in progress

### Next priorities

- Complete production ML-service deployment
- Connect frontend to production APIs
- Improve recommendation calibration
- Add stronger monitoring and observability
- Load-test the API for higher traffic
- Improve error handling and resilience

---

## 🎯 Why This Project Exists

Currency rates change constantly, but users generally have to choose between sending money immediately or waiting without knowing whether waiting is likely to help.

SmartRemit turns exchange-rate history and forecasting into a simple decision-support experience:

**Amount → Rate Intelligence → Forecast → Expected Gain → Recommendation**

It is designed as a practical engineering project rather than a demonstration that assumes a complex ML model will always outperform a simple baseline.

---

## 👩‍💻 Author

**Saptami Biswas**  
B.Tech Electrical Engineering · NIT Agartala

---

## 📜 License

MIT License

const axios = require('axios');
const Prediction = require('../models/Prediction');

const ML_SERVICE_URL = process.env.ML_SERVICE_URL;

if (!ML_SERVICE_URL) {
    throw new Error('ML_SERVICE_URL is not configured');
}

exports.getBestRoute = async (req, res) => {
    try {
        const response = await axios.post(`${ML_SERVICE_URL}/predict-route`, req.body.routes);
        res.send({ bestRoute: response.data });
    } catch (error) {
        console.error('ML Service Error (Route):', error.message);
        res.status(500).send({ error: 'Failed to fetch best route from ML service.' });
    }
};

exports.getForecast = async (req, res) => {
    try {
        const payload = {
            from_curr: req.query.from || 'USD',
            to_curr: req.query.to || 'INR',
            amount: parseFloat(req.query.amount) || 1000.0,
            days: parseInt(req.query.days) || 7
        };
        const response = await axios.post(`${ML_SERVICE_URL}/forecast`, payload);
        const data = response.data;

        try {
            await Prediction.create({
                pair: data.pair,
                amount: data.amount,
                recommendation: data.recommendation,
                expected_gain_total: data.expected_gain_total,
                best_day: data.best_day,
                trend: data.trend
            });
        } catch (dbErr) {
            console.error('History Error (MongoDB):', dbErr.message);
        }

        res.send(data);
    } catch (error) {
        console.error('ML Service Error (Forecast):', error.message);
        res.status(500).send({ error: 'Failed to fetch forecast from ML service.' });
    }
};

exports.getHistory = async (req, res) => {
    try {
        const history = await Prediction.find().sort({ createdAt: -1 }).limit(10);
        res.send({ history });
    } catch (error) {
        console.error('DB Error (History):', error.message);
        res.status(500).send({ error: 'Failed to fetch prediction history.' });
    }
};

exports.checkFraud = async (req, res) => {
    try {
        const response = await axios.post(`${ML_SERVICE_URL}/fraud-check`, req.body.transaction);
        res.send(response.data);
    } catch (error) {
        console.error('ML Service Error (Fraud):', error.message);
        res.status(500).send({ error: 'Failed to evaluate fraud status from ML service.' });
    }
};

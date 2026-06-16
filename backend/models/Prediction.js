const mongoose = require('mongoose');

const PredictionSchema = new mongoose.Schema({
    pair: String,
    amount: Number,
    recommendation: String,
    expected_gain_total: Number,
    best_day: String,
    trend: String,
    createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Prediction', PredictionSchema);

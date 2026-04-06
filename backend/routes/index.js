const express = require('express');
const router = express.Router();
const { getBestRoute, getForecast, checkFraud, getHistory } = require('../controllers/apiController');
const { signup, login } = require('../controllers/authController');
const auth = require('../middleware/auth');

// Public routes
router.post('/signup', signup);
router.post('/login', login);

// Protected routes (require valid JWT)
router.post('/route', auth, getBestRoute);
router.get('/forecast', auth, getForecast);
router.post('/fraud', auth, checkFraud);
router.get('/history', auth, getHistory);

module.exports = router;

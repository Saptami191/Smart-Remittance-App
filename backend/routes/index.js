const express = require('express');
const router = express.Router();
const { getBestRoute, getForecast, checkFraud } = require('../controllers/apiController');

router.post('/route', getBestRoute);
router.get('/forecast', getForecast);
router.post('/fraud', checkFraud);

module.exports = router;

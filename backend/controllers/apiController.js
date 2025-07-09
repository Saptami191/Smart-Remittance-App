const { spawn } = require('child_process');
const path = require('path');

exports.getBestRoute = (req, res) => {
    const py = spawn('python', [path.join(__dirname, '../../ml_model/route_selector.py')]);
    let result = '';

    py.stdin.write(JSON.stringify(req.body.routes));
    py.stdin.end();

    py.stdout.on('data', chunk => result += chunk);
    py.stderr.on('data', err => console.error(`stderr: ${err}`));
    py.on('close', () => {
        try {
            res.send({ bestRoute: JSON.parse(result) });
        } catch (e) {
            res.status(500).send({ error: 'Failed to parse best route result.' });
        }
    });
};

exports.getForecast = (req, res) => {
    const py = spawn('python', [path.join(__dirname, '../../ml_model/forecast.py')]);
    let forecast = '';
    py.stdout.on('data', data => forecast += data);
    py.stderr.on('data', err => console.error(`stderr: ${err}`));
    py.on('close', () => {
        try {
            res.send({ forecast: JSON.parse(forecast) });
        } catch (e) {
            res.status(500).send({ error: 'Failed to parse forecast data.' });
        }
    });
};

exports.checkFraud = (req, res) => {
    const transaction = JSON.stringify(req.body.transaction);
    const py = spawn('python', [path.join(__dirname, '../../ml_model/detect_fraud.py'), transaction]);
    let result = '';
    py.stdout.on('data', data => result += data);
    py.stderr.on('data', err => console.error(`stderr: ${err}`));
    py.on('close', () => {
        try {
            res.send({ isFraud: result.trim() === 'True' });
        } catch (e) {
            res.status(500).send({ error: 'Failed to evaluate fraud result.' });
        }
    });
};

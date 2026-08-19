require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');
const mongoose = require('mongoose');
const routes = require('./routes');

const app = express();
app.use(cors());
app.use(express.json());

const MONGO_URI = process.env.MONGO_URI;
const PORT = process.env.PORT || 5000;

if (!MONGO_URI) {
    console.error('CRITICAL ERROR: MONGO_URI is not defined');
    process.exit(1);
}

const connectDB = async () => {
    try {
        console.log('Attempting to connect to MongoDB Atlas...');
        await mongoose.connect(MONGO_URI, {
            serverSelectionTimeoutMS: 10000,
            family: 4,
            tls: true
        });
        console.log('MongoDB Connected Successfully');
        app.listen(PORT, '0.0.0.0', () => {
            console.log(`Server listening on port ${PORT}`);
        });
    } catch (err) {
        console.error('DATABASE CONNECTION FAILED');
        console.error('Reason:', err.message);
        process.exit(1);
    }
};

app.get('/health', (_req, res) => {
    res.json({ status: 'ok' });
});

app.use(express.static(path.join(__dirname, '../')));
app.use('/api', routes);

connectDB();

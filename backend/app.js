const dns = require('node:dns');
dns.setServers(['8.8.8.8', '8.8.4.4']); // Force Google DNS to bypass ISP blocks

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');
const mongoose = require('mongoose');
const routes = require('./routes');

const app = express();
app.use(cors());
app.use(express.json());

// --- CONFIGURATION ---
const MONGO_URI = process.env.MONGO_URI;
const PORT = process.env.PORT || 5000;

if (!MONGO_URI) {
    console.error('❌ CRITICAL ERROR: MONGO_URI is not defined in .env');
    process.exit(1);
}

const connectDB = async () => {
    try {
        console.log('⏳ Attempting to connect to MongoDB Atlas...');
        
        // Using the most compatible options for Windows/India ISP environments
        await mongoose.connect(MONGO_URI, {
            serverSelectionTimeoutMS: 10000,
            family: 4,
            tls: true
        });

        console.log('✅ MongoDB Connected Successfully');
        
        app.listen(PORT, () => {
            console.log(`🚀 Server running on http://localhost:${PORT}`);
        });

    } catch (err) {
        console.error('❌ DATABASE CONNECTION FAILED');
        console.error('Reason:', err.message);
        console.error('Please verify your .env credentials and IP Whitelist.');
        process.exit(1); 
    }
};

// Serve static files
app.use(express.static(path.join(__dirname, '../')));

// API Routes
app.use('/api', routes);

connectDB();

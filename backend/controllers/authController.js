const User = require('../models/User');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const SECRET_KEY = process.env.JWT_SECRET || 'SECRET_KEY';

exports.signup = async (req, res) => {
    try {
        const { username, email, password } = req.body;
        
        // Ensure email isn't already taken
        const existingUser = await User.findOne({ email });
        if (existingUser) {
            return res.status(409).json({ error: 'User with this email already exists' });
        }

        const hashedPassword = await bcrypt.hash(password, 10);
        
        const user = await User.create({
            username,
            email,
            password: hashedPassword
        });

        res.status(201).json({ message: 'User created successfully', userId: user._id });
    } catch (err) {
        console.error('Signup Error:', err.message);
        res.status(500).json({ error: 'Failed to create user' });
    }
};

exports.login = async (req, res) => {
    try {
        const { email, password } = req.body;
        
        const user = await User.findOne({ email });
        if (!user) {
            return res.status(401).json({ error: 'Invalid email or password' });
        }

        const isMatch = await bcrypt.compare(password, user.password);
        if (!isMatch) {
            return res.status(401).json({ error: 'Invalid email or password' });
        }

        const token = jwt.sign({ userId: user._id, email: user.email }, SECRET_KEY, { expiresIn: '24h' });

        res.json({ token, username: user.username });
    } catch (err) {
        console.error('Login Error:', err.message);
        res.status(500).json({ error: 'An internal server error occurred' });
    }
};

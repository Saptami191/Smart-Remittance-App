const jwt = require('jsonwebtoken');

module.exports = (req, res, next) => {
    // Ensuring the secret is read inside the function context 
    // to prevent undefined errors during startup.
    const SECRET_KEY = process.env.JWT_SECRET;
    const authHeader = req.headers.authorization;

    // Check if the header exists and starts with "Bearer "
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ error: 'Unauthorized: No token provided' });
    }

    // Extract the token (the string after "Bearer ")
    const token = authHeader.split(' ')[1];

    try {
        // Verify the token using the secret from your .env
        const decoded = jwt.verify(token, SECRET_KEY);
        req.user = decoded; // Attach user info to the request
        next(); // Move to the next function/route
    } catch (err) {
        console.error("JWT Error:", err.message);
        return res.status(401).json({ error: 'Unauthorized: Invalid or expired token' });
    }
};

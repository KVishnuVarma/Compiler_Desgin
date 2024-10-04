const jwt = require('jsonwebtoken');

const authMiddleware = (req, res, next) => {
    const token = req.headers['authorization'];
    if (!token) return res.status(401).send('Access denied');

    try {
        const verified = jwt.verify(token, 'secretkey');
        req.user = verified;
        next();
    } catch (err) {
        res.status(400).send('Invalid token');
    }
};

const roleMiddleware = (role) => (req, res, next) => {
    if (req.user.role !== role) {
        return res.status(403).send('Forbidden');
    }
    next();
};

module.exports = { authMiddleware, roleMiddleware };

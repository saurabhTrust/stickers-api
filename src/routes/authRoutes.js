/**
 * Authentication Routes
 */

const express = require('express');
const router = express.Router();

const { authenticateJwt } = require('../middleware/auth');
const {
  register,
  login,
  getProfile,
  refreshToken,
  logout
} = require('../controllers/userController');

// ================================
// Public Routes
// ================================

router.post('/register', register);
router.post('/login', login);

// ================================
// Protected Routes
// ================================

console.log('authenticateJWT:', authenticateJwt);
console.log('getProfile:', getProfile);
// Get current user
router.get('/me', authenticateJwt, getProfile);

// Refresh token
router.post('/token/refresh', authenticateJwt, refreshToken);

// Logout
router.post('/logout', authenticateJwt, logout);

module.exports = router;
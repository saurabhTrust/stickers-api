/**
 * Authentication Middleware
 * Supports both API Key and JWT Token authentication
 */
const jwt =require('jsonwebtoken');
const crypto = require('crypto');
const { error } = require('console');

// Load environment variables

const API_KEY = process.env.API_KEYS ? process.env.API_KEYS.split(',').map(key => key.trim()).filter(Boolean): [];

const JWT_SECRET = process.env.JWT_SECRET || 'your_jwt_secret_key';
const JWT_EXPIRY= process.env.JWT_EXPIRY || '24h';

//warn in the production if JWT_SECRET is not set or weak

if(process.env.NODE_ENV === 'production' && (!process.env.JWT_SECRET || process.env.JWT_SECRET.length < 32)){
    console.warn('Warning: JWT_SECRET is not set or is too weak. Please set a strong JWT_SECRET in production.');
}

// --------------------------------------------------
// Helper: timing safe compare (prevents timing attack)
// --------------------------------------------------

const safeCompare = (a, b) => {
    const bufA=Buffer.from(a);
    const bufB=Buffer.from(b);
    if(bufA.length !== bufB.length) return false;
    return crypto.timingSafeEqual(bufA, bufB);
};

// --------------------------------------------------
// API Key Authentication Middleware
// --------------------------------------------------

const authenticateApiKey = (req, res, next) => {
    const apiKey=req.header['x-api-key'];
    if(!apiKey){
        return res.status(401).json({
            success:false,
            error:'API key is missing',
            Messaage:'Please provide a valid API key in the x-api-key header'
        });
    }

    //timnig safe compare against all valid API keys
    const isValid=API_KEY.some(key => safeCompare(key, apiKey));

    if(!isValid){
        return res.status(401).json({
            success:false,
            error:'Invalid API key',
            Message:'The provided API key is invalid. Please check your API key and try again.'
        });
    }

    //Dont expose raw key
    req.auth ={
        method:'apiKey'
    };
    next();
}

// --------------------------------------------------
// JWT Token Authentication Middleware
// --------------------------------------------------

const authenticateJwt = (req, res, next) => {

    const authHeader=req.headers['authorization'];

    if(!authHeader || !authHeader.startsWith('Bearer ')){
        return res.status(401).json({
            success:false,
            error:'Authorization header is missing or malformed',
            Message:'Please provide a valid JWT token in the Authorization header as Bearer token'
        });
    }
    const token=authHeader.split(' ')[1];

    try{
        const decoded=jwt.verify(token,JWT_SECRET);

        req.auth={
            method:'jwt',
            user:decoded
        };
        next();
    }catch(error){
        if(error.name === 'TokenExpiredError'){
            return res.status(401).json({
                success:false,
                error:'JWT token has expired',
                Message:'Your JWT token has expired. Please obtain a new token and try again.'
            });
        }
        return res.status(401).json({
            success:false,
            error:'Invalid JWT token',
            Message:'The provided JWT token is invalid. Please check your token and try again.'
        });
    }
};


// --------------------------------------------------
// Flexible Authentication (API Key OR JWT)
// --------------------------------------------------

const authenticate = (req, res, next) => {
    const apiKey=req.headers['x-api-key'];
    const authHeader=req.headers['authorization'];

    if(apiKey){
        return authenticateApiKey(req, res, next);
    }

    if(authHeader){
        return authenticateJwt(req, res, next);
    }

    return res.status(401).json({
        success:false,
        error:'No valid authentication method provided',
        Message:'Please provide either an API key (x-api-key header) or a JWT token (Authorization header)'
    });
}


// --------------------------------------------------
// Optional Authentication Middleware (allows access but sets auth info if provided)
// --------------------------------------------------

const optionalAuth=(req, res, next) => {
    const apiKey=req.headers['x-api-key'];
    const authHeader=req.headers['authorization'];

    if(!apiKey && !authHeader){
        req.auth=null; //no auth provided
        return next();
    }

    return
};

//--------------------------------------------------
// JWT Utilities
// --------------------------------------------------

const generateToken = (payload) => {
    return jwt.sign(payload, JWT_SECRET, { 
        expiresIn: JWT_EXPIRY 
    });
};

const verifyToken = (token) => {
    try{
        return jwt.verify(token, JWT_SECRET);
    }catch(error){
        throw error;
    }
};

module.exports = {
    authenticate,
    authenticateApiKey,
    authenticateJwt,
    optionalAuth,
    generateToken,
    verifyToken,
    JWT_SECRET,
    JWT_EXPIRY
};
require('dotenv').config();
const express=require('express');
const cors=require('cors');
const multer=require('multer')
const helmet=require('helmet');
const morgan=require('morgan');
const path=require('path');
const storageService = require('./services/storageService');
const app=express();
(async () => {
  await storageService.ensureOutputDir();
})();



app.use(cors());
app.use(helmet());
app.use(morgan('dev'));
app.use(express.json());
app.use(express.urlencoded({extended:true}));

//Serve static files (for uploaded images and generated stickers)
app.use('/stickers', express.static(path.join(__dirname, '../uploads/stickers')));

//Routes
const imageRoutes=require('./routes/imageRoutes');
const authRoutes=require('./routes/authRoutes');
const errorHandler=require('./middleware/errorHandler');

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    message: 'Sticker Generation API',
    version: '1.0.0',
    authentication: 'enabled',
    endpoints: {
      auth: {
        register: 'POST /api/auth/register',
        login: 'POST /api/auth/login',
        profile: 'GET /api/auth/profile (requires auth)',
        refresh: 'POST /api/auth/refresh (requires auth)'
      },
      stickers: {
        image_upload: 'POST /api/upload (requires auth)',
        text_generation: 'POST /api/generate-text (requires auth)',
        job_status: 'GET /api/status/:jobId (optional auth)',
        queue_stats: 'GET /api/stats (optional auth)'
      }
    },
    auth_methods: {
      api_key: 'X-API-Key header',
      jwt: 'Authorization: Bearer <token>'
    }
  });
});

//API routes
app.use('/api/auth',authRoutes);
app.use('/api',imageRoutes);

//Error handling middleware
app.use(errorHandler);


if (!process.env.PORT) {
  throw new Error("PORT not loaded from .env");
}
const PORT=process.env.PORT;

app.listen(PORT,()=>{
    console.log("server is running on port "+PORT);
    console.log(`http://localhost:${PORT}`);
    console.log(`Authentication endpoints: POST http://localhost:${PORT}/api/auth/register and POST http://localhost:${PORT}/api/auth/login`);
    console.log(` Upload endpoint: POST http://localhost:${PORT}/api/upload`);
    console.log(` Text-based sticker generation endpoint: POST http://localhost:${PORT}/api/generate-text-stickers`);
})



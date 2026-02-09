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
const errorHandler=require('./middleware/errorHandler');

// Sample route
app.get('/',(req,res)=>{
    res.send('Hello World!');
}); 

//API routes
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
    console.log(` Upload endpoint: POST http://localhost:${PORT}/api/upload`);
})


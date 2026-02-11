const express = require('express');
const router=express.Router();
const upload=require('../middleware/uploadMIddleware');
const validateImage=require('../middleware/validation');
const validateTextInput=require('../middleware/textValidation');
const {uploadImage,generateTextStickers,getStatus,getStats}=require('../controllers/imageControllers');

//Route to handle image upload
router.post(
    '/upload',
    upload.single('image'), //Handle single file upload with field name 'image'
    validateImage, //Validate uploaded file
    uploadImage //Controller to process the upload and respond
);

//Text Based sticker generation
router.post(
    '/generate-text-stickers',
    validateTextInput,
    generateTextStickers
);


//GET route to check job status
router.get('/status/:jobId',getStatus);

//GET route to get queue stats
router.get('/stats',getStats);


module.exports=router;






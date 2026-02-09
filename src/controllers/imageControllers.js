// const fs=require('fs');
// const upload = require('../middleware/uploadMIddleware');
// const imageProcessor = require('../services/imageProcessor');
// const gpuService=require('../services/gpuService');
// const storageService=require('../services/storageService');


// //upload and process image

// const uploadImage= async(req,res)=>{

//     let uploadFilePath=null;
//     let preprocessedImage=null;
//     try{
//         console.log('Image received:',req.file.filename);
//         console.log('metadata:',req.imageMetadata);

//         uploadFilePath=req.file.path;

//         //STEP 1: Preprocess image (resize, convert to PNG, etc.)
//         preprocessedFilePath=await imageProcessor.preprocessImage(uploadFilePath);

//         //STEP 2: Read preprocessed image and convert to Base64
//         const base64Image=await imageProcessor.imageToBase64(preprocessedFilePath);

//         //STEP 3: Send Base64 image to GPU server for sticker generation
//         const gpuResult=await gpuService.generateStickers(base64Image);

//         //STEP 44: Save generated stickers and get their URLs
//         const stickerUrls=await storageService.saveStickers(gpuResult.stickers,req);

//         //STEP 5:clean up the temporary files
//         await imageProcessor.cleanup([uploadFilePath, preprocessedFilePath]);

//         //STEP 6: Return sticker URLs in response
//             res.status(200).json({
//                 success:true,  
//                 message:'Stickers generated successfully',
//                 data:{
//                     stickers:stickerUrls,
//                     count:stickerUrls.length,
//                     processingTime:gpuResult.processingTime
//                 }
//             });
//         // For now, just return success response
//         // We'll add GPU processing in next step
//         // res.status(200).json({
//         //     success:true,
//         //     message:'Image uploaded and validated successfully',
//         //     data:{
//         //         filename:req.file.filename,
//         //         originalname:req.file.originalname,
//         //         size:req.file.size,
//         //         dimensions:{
//         //             width:req.imageMetadata.width,
//         //             height:req.imageMetadata.height
//         //         },
//         //         format:req.imageMetadata.format,
//         //     }
//         // });
//     }catch (error) {
//     console.error(' Error in uploadImage:', error);
    
//     // Clean up files on error
//     const filesToClean = [uploadedFilePath, preprocessedFilePath].filter(Boolean);
//     await imageProcessor.cleanup(filesToClean);
    
//     // Return appropriate error
//     if (error.message.includes('GPU server')) {
//       return res.status(503).json({
//         success: false,
//         error: 'GPU service unavailable',
//         message: error.message
//       });
//     }

//     res.status(500).json({
//       success: false,
//       error: 'Failed to generate stickers',
//       message: process.env.NODE_ENV === 'development' ? error.message : undefined
//     });
//   }
// };

// module.exports=uploadImage;


// const imageProcessor = require('../services/imageProcessor');
// const gpuService = require('../services/gpuService');
// const storageService = require('../services/storageService');

// // Upload and process image
// const uploadImage = async (req, res) => {
//   let uploadedFilePath = null;
//   let preprocessedFilePath = null;

//   try {
//     console.log('Image received:', req.file.filename);
//     console.log('metadata:', req.imageMetadata);

//     // STEP 0: store uploaded file path
//     uploadedFilePath = req.file.path;

//     // STEP 1: Preprocess image
//     preprocessedFilePath =
//       await imageProcessor.preprocessImage(uploadedFilePath);

//     // STEP 2: Convert preprocessed image to Base64
//     const base64Image =
//       await imageProcessor.imageToBase64(preprocessedFilePath);

//     // STEP 3: Send to GPU
//     const gpuResult =
//       await gpuService.generateStickers(base64Image);

//     // STEP 4: Save stickers
//     const stickerUrls =
//       await storageService.saveStickers(gpuResult.stickers, req);

//     // STEP 5: Cleanup temp files
//     await imageProcessor.cleanup([
//       uploadedFilePath,
//       preprocessedFilePath
//     ]);

//     // STEP 6: Respond
//     return res.status(200).json({
//       success: true,
//       message: 'Stickers generated successfully',
//       data: {
//         stickers: stickerUrls,
//         count: stickerUrls.length,
//         processingTime: gpuResult.processingTime
//       }
//     });

//   } catch (error) {
//     console.error(' Error in uploadImage:', error.message);

//     // Cleanup on failure
//     await imageProcessor.cleanup(
//       [uploadedFilePath, preprocessedFilePath].filter(Boolean)
//     );

//     if (error.message.includes('GPU')) {
//       return res.status(503).json({
//         success: false,
//         error: 'GPU service unavailable',
//         message: error.message
//       });
//     }

//     return res.status(500).json({
//       success: false,
//       error: 'Failed to generate stickers',
//       message:
//         process.env.NODE_ENV === 'development'
//           ? error.message
//           : undefined
//     });
//   }
// };

// module.exports = uploadImage;


const fs = require('fs').promises;
const { v4: uuidv4 } = require('uuid');
const { addStickerJob, getJobStatus, getQueueStats } = require('../services/queueService');
const jobStorage = require('../services/jobStorage');

// Upload and queue image processing
const uploadImage = async (req, res) => {
  try {
    console.log('Image received:', req.file.filename);
    console.log('Metadata:', req.imageMetadata);
    console.log(' Parameters:', req.body);

    const jobId = uuidv4();
    const uploadedFilePath = req.file.path;

    // Store job metadata
    await jobStorage.storeJobMetadata(jobId, {
      originalName: req.file.originalname,
      uploadedAt: new Date().toISOString(),
  
      dimensions: req.imageMetadata
    });

    // Add job to queue
    const job = await addStickerJob({
      jobId: jobId,
      imagePath: uploadedFilePath,
    });

    // Return job ID immediately
    res.status(202).json({
      success: true,
      message: 'Job queued successfully',
      data: {
        jobId: jobId,
        status: 'queued',
        statusUrl: `/api/status/${jobId}`,
        estimatedTime: '30-60 seconds'
      }
    });

  } catch (error) {
    console.error(' Error in uploadImage:', error);
    
    // Clean up uploaded file on error
    if (req.file && req.file.path) {
      await fs.unlink(req.file.path).catch(() => {});
    }
    
    res.status(500).json({
      success: false,
      error: 'Failed to queue job',
      message: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
};

// Get job status
const getStatus = async (req, res) => {
  try {
    const { jobId } = req.params;

    const jobStatus = await getJobStatus(jobId);

    if (!jobStatus) {
      return res.status(404).json({
        success: false,
        error: 'Job not found'
      });
    }

    // Build response based on job state
    const response = {
      success: true,
      jobId: jobId,
      status: jobStatus.state,
      progress: jobStatus.progress || 0
    };

    // If completed, add sticker URLs
    if (jobStatus.state === 'completed' && jobStatus.result) {
      const baseUrl = `${req.protocol}://${req.get('host')}`;
      const stickerUrls = jobStatus.result.stickers.map(s => 
        `${baseUrl}/stickers/${s.filename}`
      );

      // Store URLs in Redis
      await jobStorage.storeStickerUrls(jobId, stickerUrls);

      response.stickers = stickerUrls;
      response.processingTime = jobStatus.result.processingTime;
      response.completedAt = jobStatus.result.completedAt;
    }

    // If failed, add error info
    if (jobStatus.state === 'failed') {
      response.error = jobStatus.failedReason;
      response.attempts = jobStatus.attemptsMade;
    }

    // Add metadata
    const metadata = await jobStorage.getJobMetadata(jobId);
    if (metadata) {
      response.metadata = metadata;
    }

    res.json(response);

  } catch (error) {
    console.error(' Error in getStatus:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get job status'
    });
  }
};

// Get queue statistics
const getStats = async (req, res) => {
  try {
    const stats = await getQueueStats();
    
    res.json({
      success: true,
      queue: stats,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error(' Error in getStats:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get queue stats'
    });
  }
};

module.exports = {
  uploadImage,
  getStatus,
  getStats
};
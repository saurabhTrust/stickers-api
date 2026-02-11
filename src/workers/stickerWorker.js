// const { stickerQueue } = require('../services/queueService');
// const imageProcessor = require('../services/imageProcessor');
// const gpuService = require('../services/gpuService');
// const textGpuService = require('../services/textGpuService');
// const fs = require('fs').promises;

// // Process sticker generation jobs
// stickerQueue.process('generate-stickers', async (job) => {
//   const { jobId, imagePath,type,textData} = job.data;
  
//   let preprocessedPath = null;
  
//   try {
//     console.log(`\n Processing job ${jobId}`);
    
//     // Update progress: 10%
//     await job.progress(10);
    
//     // Step 1: Preprocess image
//     console.log(' Preprocessing image...');
//     preprocessedPath = await imageProcessor.preprocessImage(imagePath);
//     await job.progress(30);
    
//     // Step 2: Convert to base64
//     console.log('Converting to base64...');
//     const base64Image = await imageProcessor.imageToBase64(preprocessedPath);
//     await job.progress(40);
    
//     // Step 3: Send to GPU
//     console.log('Sending to GPU server...');
//     const gpuResult = await gpuService.generateStickers(base64Image);
//     await job.progress(70);
    
//     // Step 4: Save stickers to disk
//     console.log('Saving stickers...');
//     const savedStickers = [];
    
//     for (let i = 0; i < gpuResult.stickers.length; i++) {
//       const sticker = gpuResult.stickers[i];
//       const filename = `sticker-${jobId}-${i + 1}.png`;
      
//       const filePath = await imageProcessor.base64ToImage(
//         sticker.image,
//         filename
//       );
      
//       savedStickers.push({
//         filename: filename,
//         path: filePath,
//         index: i + 1
//       });
//     }
    
//     await job.progress(90);
    
//     // Step 5: Clean up temporary files
//     console.log('🧹 Cleaning up...');
//     await imageProcessor.cleanup([imagePath, preprocessedPath]);
//     await job.progress(100);
    
//     console.log(`Job ${jobId} completed successfully`);
    
//     // Return result
//     return {
//       success: true,
//       jobId: jobId,
//       stickers: savedStickers,
//       processingTime: gpuResult.processingTime,
//       completedAt: new Date().toISOString()
//     };
    
//   } catch (error) {
//     console.error(`Job ${jobId} failed:`, error.message);
    
//     // Clean up on error
//     const filesToClean = [imagePath, preprocessedPath].filter(Boolean);
//     await imageProcessor.cleanup(filesToClean);
    
//     throw error; // Bull will handle retries
//   }
// });

// console.log('Sticker worker is ready and listening for jobs...');

// module.exports = stickerQueue;

const { stickerQueue } = require('../services/queueService');
const imageProcessor = require('../services/imageProcessor');
const gpuService = require('../services/gpuService');
const textGpuService = require('../services/textGpuService');  // NEW
const fs = require('fs').promises;

// Process both image and text jobs
stickerQueue.process('generate-stickers', async (job) => {
  const { jobId, type, imagePath, textData } = job.data;
  
  try {
    console.log(`\nProcessing ${type || 'image'} job ${jobId}`);
    
    // Route to appropriate processor based on type
    if (type === 'text') {
      return await processTextJob(job);
    } else {
      return await processImageJob(job);
    }
    
  } catch (error) {
    console.error(`Job ${jobId} failed:`, error.message);
    throw error;
  }
});

// NEW: Process text-based jobs
async function processTextJob(job) {
  const { jobId, textData } = job.data;
  
  // VALIDATE HERE
  if (!textData || (!textData.text && !textData.keywords)) {
    throw new Error('Invalid text input');
  }
  
  try {
    await job.progress(10);
    
    // Step 1: Send to GPU
    console.log('Sending text to GPU server...');
    const gpuResult = await textGpuService.generateTextStickers(textData);
    await job.progress(50);
    
    // Step 2: Save stickers
    console.log('Saving text stickers...');
    const savedStickers = [];
    
    for (let i = 0; i < gpuResult.stickers.length; i++) {
      const sticker = gpuResult.stickers[i];
      const filename = `text-sticker-${jobId}-${i + 1}.png`;
      
      const filePath = await imageProcessor.base64ToImage(
        sticker.image,
        filename
      );
      
      savedStickers.push({
        filename: filename,
        path: filePath,
        index: i + 1
      });
    }
    
    await job.progress(90);
    await job.progress(100);
    
    console.log(`Text job ${jobId} completed - ${savedStickers.length} stickers`);
    
    return {
      success: true,
      jobId: jobId,
      type: 'text',
      stickers: savedStickers,
      processingTime: gpuResult.processingTime,
      completedAt: new Date().toISOString()
    };
    
  } catch (error) {
    console.error(`Text job ${jobId} failed:`, error.message);
    throw error;
  }
}

// Existing: Process image-based jobs
async function processImageJob(job) {
  const { jobId, imagePath } = job.data;
  let preprocessedPath = null;
  
  try {
    await job.progress(10);
    
    // Step 1: Preprocess image
    console.log('Preprocessing image...');
    preprocessedPath = await imageProcessor.preprocessImage(imagePath);
    await job.progress(30);
    
    // Step 2: Convert to base64
    console.log('Converting to base64...');
    const base64Image = await imageProcessor.imageToBase64(preprocessedPath);
    await job.progress(40);
    
    // Step 3: Send to GPU
    console.log(' Sending to GPU server...');
    const gpuResult = await gpuService.generateStickers(base64Image);
    await job.progress(70);
    
    // Step 4: Save stickers
    console.log(' Saving stickers...');
    const savedStickers = [];
    
    for (let i = 0; i < gpuResult.stickers.length; i++) {
      const sticker = gpuResult.stickers[i];
      const filename = `sticker-${jobId}-${i + 1}.png`;
      
      const filePath = await imageProcessor.base64ToImage(
        sticker.image,
        filename
      );
      
      savedStickers.push({
        filename: filename,
        path: filePath,
        index: i + 1
      });
    }
    
    await job.progress(90);
    
    // Step 5: Clean up
    console.log(' Cleaning up...');
    await imageProcessor.cleanup([imagePath, preprocessedPath]);
    await job.progress(100);
    
    console.log(` Image job ${jobId} completed - ${savedStickers.length} stickers`);
    
    return {
      success: true,
      jobId: jobId,
      type: 'image',
      stickers: savedStickers,
      processingTime: gpuResult.processingTime,
      completedAt: new Date().toISOString()
    };
    
  } catch (error) {
    const filesToClean = [imagePath, preprocessedPath].filter(Boolean);
    await imageProcessor.cleanup(filesToClean);
    throw error;
  }
}

console.log(' Sticker worker is ready and listening for jobs...');
console.log(' Supports: image-based and text-based sticker generation');

module.exports = stickerQueue;
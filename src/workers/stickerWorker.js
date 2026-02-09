const { stickerQueue } = require('../services/queueService');
const imageProcessor = require('../services/imageProcessor');
const gpuService = require('../services/gpuService');
const fs = require('fs').promises;

// Process sticker generation jobs
stickerQueue.process('generate-stickers', async (job) => {
  const { jobId, imagePath } = job.data;
  
  let preprocessedPath = null;
  
  try {
    console.log(`\n Processing job ${jobId}`);
    
    // Update progress: 10%
    await job.progress(10);
    
    // Step 1: Preprocess image
    console.log(' Preprocessing image...');
    preprocessedPath = await imageProcessor.preprocessImage(imagePath);
    await job.progress(30);
    
    // Step 2: Convert to base64
    console.log('Converting to base64...');
    const base64Image = await imageProcessor.imageToBase64(preprocessedPath);
    await job.progress(40);
    
    // Step 3: Send to GPU
    console.log('Sending to GPU server...');
    const gpuResult = await gpuService.generateStickers(base64Image);
    await job.progress(70);
    
    // Step 4: Save stickers to disk
    console.log('Saving stickers...');
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
    
    // Step 5: Clean up temporary files
    console.log('🧹 Cleaning up...');
    await imageProcessor.cleanup([imagePath, preprocessedPath]);
    await job.progress(100);
    
    console.log(`Job ${jobId} completed successfully`);
    
    // Return result
    return {
      success: true,
      jobId: jobId,
      stickers: savedStickers,
      processingTime: gpuResult.processingTime,
      completedAt: new Date().toISOString()
    };
    
  } catch (error) {
    console.error(`Job ${jobId} failed:`, error.message);
    
    // Clean up on error
    const filesToClean = [imagePath, preprocessedPath].filter(Boolean);
    await imageProcessor.cleanup(filesToClean);
    
    throw error; // Bull will handle retries
  }
});

console.log('Sticker worker is ready and listening for jobs...');

module.exports = stickerQueue;
const sharp = require('sharp');
const fs = require('fs').promises;
const path = require('path');

class ImageProcessor {
    constructor() {
        this.targetSize=512; // Target size for resizing (512x512)
        this.tempDir=process.env.TEMP_DIR || './temp'; // Temporary directory for processing
        this.outputFormat = process.env.MODEL_IMAGE_FORMAT || 'png';
    }

    //call this ONCE during server startup to ensure temp directory exists
    async init(){
        await this.ensureTempDir();
    }

    async ensureTempDir() {
        try{
            await fs.access(this.tempDir);
        }catch(err){
            await fs.mkdir(this.tempDir, { recursive: true });
        }
    }

    /**
   * Preprocess image for ML model
   * - Fix orientation
   * - Resize to target size
   * - Normalize format
   */
  async preprocessImage(inputPath) {
    try{
        await this.ensureTempDir();
        console.log(`Preprocessing image: ${inputPath}`);

        const filename=`processed-${Date.now()}.${this.outputFormat}`; // Use first format from supported list
        const outputPath=path.join(this.tempDir, filename);

        let pipeline=sharp(inputPath)
            .rotate() // Auto-rotate based on EXIF data
            .resize(this.targetSize, this.targetSize, {
                fit: 'cover', // Crop to fit target size
                position: 'center' // Center the crop
            });
            if(this.outputFormat === 'jpg' || this.outputFormat === 'jpeg'){
                pipeline= pipeline.jpeg({ quality: 90 }); // Adjust quality for JPEG
            }else if(this.outputFormat === 'png'){
                pipeline= pipeline.png({ compressionLevel: 9 }); // Max compression for PNG
            }else if(this.outputFormat === 'webp'){
                pipeline= pipeline.webp({ quality: 90 }); // Adjust quality for WebP
            }

            await pipeline.toFile(outputPath);
            console.log(`Image processed and saved to: ${outputPath}`);
            return outputPath;
        }catch(error){
            console.error(`Error processing image: ${error.message}`);
            throw new Error(`Failed to process image: ${error.message}`)    ;
        }
    }  

    /**
   * Convert image to Base64 (for remote GPU APIs)
   */
    async imageToBase64(imagePath) {
        try{
            const imageBuffer=await fs.readFile(imagePath);
            return imageBuffer.toString('base64');
        }catch(error){
            console.error(`Error converting image to Base64: ${error.message}`);
            throw new Error(`Failed to convert image to Base64: ${error.message}`);
        }
    }

     /**
   * Convert Base64 back to image file
   */
    async base64ToImage(base64String, outputFilename) {
        try{
            const buffer=Buffer.from(base64String, 'base64');
            const outputPath=path.join(this.tempDir, outputFilename);

            await fs.writeFile(outputPath, buffer);
            return outputPath;
        }catch(error){
            console.error(`Error converting Base64 to image: ${error.message}`);
            throw new Error(`Failed to convert Base64 to image: ${error.message}`);
        }
    }

    /**
   * Optimize sticker image for web / chat usage
   */
  async optimizeSticker(inputPath, outputPath) {
    try{
        await sharp(inputPath)
            .resize(this.targetSize, this.targetSize, {
                fit: 'contain', // Ensure the entire image fits within target size
                position: 'center',
                background: { r: 0, g: 0, b: 0, alpha: 0 } // Transparent background for PNG WebP
            })
            .toFormat(this.outputFormat, { quality: 9 }) // Use first supported format with quality settings
            .toFile(outputPath);
        console.log(`Sticker optimized and saved to: ${outputPath}`);
        return outputPath;
    }catch(error){
        console.error(`Error optimizing sticker: ${error.message}`);
        throw new Error(`Failed to optimize sticker: ${error.message}`);
    }
  }
  /**
   * Cleanup temporary files
   */
  async cleanup(filePaths=[]) {
        for(const filePath of filePaths) {
            if(!filePath) continue; // Skip if no file path provided)

            await fs.unlink(filePath).catch(()=>{
                console.warn(`Failed to delete temp file: ${filePath}. It may not exist.`);
            });
        }
        console.log(`Cleanup completed for files: ${filePaths.join(', ')}`);
    }

}
module.exports=new ImageProcessor();
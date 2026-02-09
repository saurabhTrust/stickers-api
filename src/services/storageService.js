const fs = require('fs').promises;
const path = require('path');


class StorageService {
    constructor() {
        this.outputDir='./uploads/stickers'; // Directory to save generated stickers
    }

     /**
   * Call once during server startup
   */

    async init() {
        await this.ensureOutputDir();
    }

     /**
   * Ensure stickers output directory exists
   */
    async ensureOutputDir() {
        await fs.mkdir(this.outputDir, { recursive: true });
    }

    /**
   * Save a single sticker (Base64 → file)
   * Returns saved file path
   */
    // async saveSticker(base64Data, filename) {
    //     try{
    //         const buffer =Buffer.from(base64Data, 'base64');
    //         const filePath=path.join(this.outputDir, filename);

    //         await fs.writeFile(filePath, buffer);

    //         console.log('Saved sticker:', filePath);
    //         return filePath;
    //     }catch(error){
    //         console.error('Error saving sticker:', error.message);
    //         throw new Error('Failed to save sticker');
    //     }
    // }

   async saveSticker(base64Data, filename) {
  try {
    if (typeof base64Data !== 'string') {
      throw new Error(`Invalid base64 data type: ${typeof base64Data}`);
    }

    //  GUARANTEE DIRECTORY EXISTS
    await this.ensureOutputDir();

    const buffer = Buffer.from(base64Data, 'base64');
    const filePath = path.join(this.outputDir, filename);

    await fs.writeFile(filePath, buffer);

    console.log('💾 Sticker saved:', filePath);
    return filePath;
  } catch (error) {
    console.error('Error saving sticker:', error.message);
    throw new Error('Failed to save sticker');
  }
}


    /**
   * Generate public URL for a sticker
   * (Local dev version)
   */
    getStickerUrl(filename,req) {
        const protocl=req.protocol;
        const host=req.get('host');
        return `${protocl}://${host}/stickers/${filename}`;
    }

     /**
   * Save multiple stickers returned by GPU
   * Returns array of public URLs
   */

    // async saveStickers(stickersBase64,req){
    //     try{
    //         const stickerUrls=[];

    //         for(let i=0;i<stickersBase64.length;i++){
    //             const base64Image=stickersBase64[i];

    //             //skip empty or invalid images
    //             if(!base64Image) continue;
            
    //             const filename=`sticker_${Date.now()}_${i}.png`;
    //             await this.saveSticker(base64Image, filename);
    //             const url=this.getStickerUrl(filename,req);
    //             stickerUrls.push(url);
    //         }
    //         return stickerUrls;

    //     }catch(error){
    //         console.error('Error saving stickers:', error.message);
    //         throw new Error('Failed to save stickers');
    //     }
    // }

    async saveStickers(stickersFromGpu, req) {
  try {
    const stickerUrls = [];

    for (let i = 0; i < stickersFromGpu.length; i++) {
      const sticker = stickersFromGpu[i];

      //  STRICT EXTRACTION
      const base64Image = sticker?.image;

      if (typeof base64Image !== 'string') {
        console.warn('Skipping invalid sticker:', sticker);
        continue;
      }

      const filename = `sticker_${Date.now()}_${i + 1}.png`;

      await this.saveSticker(base64Image, filename);
      const url = this.getStickerUrl(filename, req);
      stickerUrls.push(url);
    }

    return stickerUrls;
  } catch (error) {
    console.error('Error saving stickers:', error.message);
    throw new Error('Failed to save stickers');
  }
}


}

module.exports = new StorageService();
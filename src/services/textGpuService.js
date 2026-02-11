const axios = require('axios');

class TextGpuService{
    constructor() {
        this.gpuUrl = process.env.GPU_TEXT_SERVER_URL || 'http://localhost:5001/api/generate-text-stickers'; // URL of the GPU processing API for text-based stickers
        this.timeout=parseInt(process.env.GPU_TEXT_TIMEOUT) || 60000; // Timeout for GPU API requests (default 60 seconds)
    }
    /**
   * Send text/keywords to GPU server for sticker generation
   */

    async generateTextStickers(textData){
        try{
            console.log('Sending text data to GPU server for sticker generation...');
            console.log('GPU Server URL:', this.gpuUrl);
            console.log('Text data:', textData);

            const startTime = Date.now();

            const response=await axios.post(
                this.gpuUrl,
                {
                    text: textData.text,
                    keywords:textData.keywords
                },{
                    timeout: this.timeout,
                    headers:{
                        'Content-Type': 'application/json'
                    }
                }
            );
            const processingTime=((Date.now() - startTime) / 1000).toFixed(2); // in seconds
            console.log('GPU processing time:', processingTime, 'seconds');
            
            return {
                success:true,
                stickers:response.data.stickers,
                processingTime: processingTime
            };
        }catch(error){

            console.error('Error communicating with GPU server:', error.message);

            if(error.code === 'ECONNREFUSED'){
                throw new Error('GPU server is not running. Please start the GPU server and try again.');
            }

            if(error.code=='ETIMEDOUT' || error.code === 'ECONNABORTED'){
                throw new Error('GPU server request timed out. Please try again later.');
            }

            if (error.response) {
                throw new Error(
                    `GPU server error: ${error.response.data.message || error.response.statusText}`
                );
            }
           throw new Error('Failed to generate stickers');  
        }
    }
}
module.exports= new TextGpuService();
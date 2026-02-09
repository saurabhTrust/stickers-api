const axios = require('axios');
const { parse } = require('dotenv');
const { response} = require('express');

class GPUService {
    constructor() {
        this.gpuUrl = process.env.GPU_SERVER_URL || 'http://localhost:5000/api/generate-stickers'; // URL of the GPU processing API
        this.timeout=parseInt(process.env.GPU_API_TIMEOUT) || 60000; // Timeout for GPU API requests (default 30 seconds)
    }
    /**
   * Send image to GPU server for sticker generation
   */
    async generateStickers(base64Image) {
        try{
            console.log('Sending image to GPU server for sticker generation...');
            console.log('GPU Server URL:', this.gpuUrl);

            const startTime = Date.now();
            const response =await axios.post(
                this.gpuUrl,
                {
                    image: base64Image
                },
                {
                    timeout: this.timeout,
                    headers:{
                        'Content-Type': 'application/json'
                    }
                }
            );

            const processingTime=((Date.now() - startTime) / 1000).toFixed(2); // in seconds
            console.log('GPU processing time:', processingTime, 'seconds');

            if (!response.data || !Array.isArray(response.data.stickers)) {
                throw new Error('Invalid GPU response format');
            }
            return {
                success: true,
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

module.exports =new GPUService();

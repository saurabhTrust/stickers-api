const Queue = require('bull');
const Redis = require('ioredis');
const { timeout } = require('./gpuService');

//Redis configuration
//create Queue instance

const stickerQueue = new Queue('sticker-generation', {
  redis: {
    host: process.env.REDIS_HOST || '127.0.0.1',
    port: process.env.REDIS_PORT || 6379,
    password: process.env.REDIS_PASSWORD || undefined
  },
  defaultJobOptions: {
    attempts: parseInt(process.env.MAX_JOB_RETRIES) || 3,
    timeout: parseInt(process.env.JOB_TIMEOUT) || 300000,
    removeOnComplete: 100,
    removeOnFail: 200
  }
});


//Queue event listeners for logging and monitoring
stickerQueue.on('error', (error) => {
    console.error('Queue error:', error);
});

stickerQueue.on('waiting', (jobId) => {
    console.log(`Job ${jobId} is waiting to be processed...`);
});

stickerQueue.on('active',(jobId) => {     
    console.log(`Job ${jobId} is now active...`);  
});
stickerQueue.on('completed', (job, result) => {
    console.log(`Job ${job.id} completed successfully.`);
});

stickerQueue.on('failed', (job, err) => {
    console.error(`Job ${job.id} failed with error:`, err.message);
});

stickerQueue.on('stalled', (job) => {
    console.warn(`Job ${job.id} stalled and will be reprocessed.`);
});


//Function to add a job to the queue
async function addStickerJob(jobData) {
    try{
        const job=await stickerQueue.add('generate-stickers', 
        jobData,{
            jobId:jobData.jobId // Use a unique identifier for the job
        });
        console.log(`Added job ${job.id} to the queue with data:`, jobData);
        return job;
    } catch (error) {
        console.error('Error adding job to queue:', error.message);
        throw error;
    }
}

// Get job status

async function getJobStatus(jobId) {
    try{
        const job=await stickerQueue.getJob(jobId);
        if(!job){
            return { status: 'not found' };
        }
        const state=await job.getState();
        const progress=job.progress();
        const failedReason=job.failedReason;
        return {
            id: job.id,
            state: state,
            progress: progress,
            data: job.data,
            result: job.returnvalue,
            failedReason: failedReason,
            attemptsMade: job.attemptsMade,
            processedOn: job.processedOn,
            finishedOn: job.finishedOn
        };
    } catch (error) {       
        console.error('Error getting job status:', error.message);
        throw error;
    }
}

//Remove job
async function removeJob(jobId) {
    try {
        const job = await stickerQueue.getJob(jobId);
        if (job) {
            await job.remove();
            console.log(`Removed job ${jobId}`);
        } else {
            console.warn(`Job ${jobId} not found`);
        }
    } catch (error) {
        console.error('Error removing job:', error.message);
        throw error;
    }
}

// Get queue stats
async function getQueueStats() {
    try {
        const [waiting, active, completed, failed, delayed] = await Promise.all([
            stickerQueue.getWaitingCount(),
            stickerQueue.getActiveCount(),
            stickerQueue.getCompletedCount(),
            stickerQueue.getFailedCount(),
            stickerQueue.getDelayedCount()
        ]);
        return {
            waiting,
            active,
            completed,
            failed,
            delayed,
            total: waiting + active + completed + failed + delayed
        };
    }catch (error) {       
        console.error('Error getting queue stats:', error.message);
        throw error;
    }
}

module.exports = {
    stickerQueue,
    addStickerJob,
    getJobStatus,
    removeJob,
    getQueueStats
};
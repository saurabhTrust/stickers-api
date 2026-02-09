const Redis = require('ioredis');

class JobStorage {
  constructor() {
    this.redis = new Redis({
      host: process.env.REDIS_HOST || 'localhost',
      port: process.env.REDIS_PORT || 6379,
      password: process.env.REDIS_PASSWORD || undefined
    });
  }

  /**
   * Store job metadata
   */
  async storeJobMetadata(jobId, metadata) {
    try {
      const key = `job:${jobId}:metadata`;
      await this.redis.set(key, JSON.stringify(metadata), 'EX', 86400); // 24h expiry
      console.log(`Metadata stored for job ${jobId}`);
    } catch (error) {
      console.error('Failed to store metadata:', error);
    }
  }

  /**
   * Get job metadata
   */
  async getJobMetadata(jobId) {
    try {
      const key = `job:${jobId}:metadata`;
      const data = await this.redis.get(key);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Failed to get metadata:', error);
      return null;
    }
  }

  /**
   * Store sticker URLs for a job
   */
  async storeStickerUrls(jobId, urls) {
    try {
      const key = `job:${jobId}:stickers`;
      await this.redis.set(key, JSON.stringify(urls), 'EX', 86400);
      console.log(`Sticker URLs stored for job ${jobId}`);
    } catch (error) {
      console.error('Failed to store URLs:', error);
    }
  }

  /**
   * Get sticker URLs for a job
   */
  async getStickerUrls(jobId) {
    try {
      const key = `job:${jobId}:stickers`;
      const data = await this.redis.get(key);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Failed to get URLs:', error);
      return null;
    }
  }

  /**
   * Delete job data
   */
  async deleteJobData(jobId) {
    try {
      await this.redis.del(`job:${jobId}:metadata`);
      await this.redis.del(`job:${jobId}:stickers`);
      console.log(`🗑️  Job data deleted for ${jobId}`);
    } catch (error) {
      console.error('Failed to delete job data:', error);
    }
  }
}

module.exports = new JobStorage();
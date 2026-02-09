require('dotenv').config();
const stickerWorker = require('./workers/stickerWorker');

console.log(' Starting sticker worker...');
console.log(` Redis: ${process.env.REDIS_HOST}:${process.env.REDIS_PORT}`);
console.log(` GPU Server: ${process.env.GPU_SERVER_URL}`);

// Handle graceful shutdown
process.on('SIGTERM', async () => {
  console.log('\n Received SIGTERM, closing worker gracefully...');
  await stickerWorker.close();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('\n Received SIGINT, closing worker gracefully...');
  await stickerWorker.close();
  process.exit(0);
});
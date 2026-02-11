# 🎨 Sticker Generation API

A production-grade asynchronous image processing API that generates multiple sticker variations from uploaded images or text input using GPU-powered ML models.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Development](#development)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This API provides two modes of sticker generation:

1. **Image-Based**: Upload an image and generate stylized sticker variations
2. **Text-Based**: Provide text or keywords and generate text stickers

The system uses an asynchronous architecture with job queues to handle long-running ML inference without blocking user requests.

### Key Capabilities

- ✅ Dual-mode operation (image and text)
- ✅ Asynchronous processing with job queues
- ✅ Real-time job progress tracking
- ✅ Automatic retry on failures
- ✅ Horizontally scalable architecture
- ✅ Production-ready error handling
- ✅ File validation and security

---

## ✨ Features

### User Features
- Upload images via REST API
- Generate stickers from text/keywords
- Get instant job ID response
- Poll for job status and progress
- Retrieve generated stickers via URLs
- Download stickers directly

### Technical Features
- **Asynchronous Processing**: Non-blocking requests using Redis queue
- **Job Persistence**: Jobs survive server crashes
- **Automatic Retries**: Failed jobs retry up to 3 times
- **Progress Tracking**: Real-time progress updates (0-100%)
- **Error Handling**: Graceful failure with clear error messages
- **Validation**: Image format, size, dimension, and text validation
- **Rate Limiting**: Protection against abuse
- **Logging**: Comprehensive request and error logging
- **Scalability**: Add more workers for parallel processing

---

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP POST
       ↓
┌──────────────────────┐
│   API Server         │
│  (Express.js)        │
│  - File upload       │
│  - Validation        │
│  - Job creation      │
└──────┬───────────────┘
       │
       ↓
┌──────────────────────┐
│   Redis Queue        │
│  (Bull)              │
│  - Job storage       │
│  - Job metadata      │
└──────┬───────────────┘
       │
       ↓
┌──────────────────────┐
│   Worker Process     │
│  - Image preprocess  │
│  - GPU communication │
│  - Sticker storage   │
└──────┬───────────────┘
       │
       ↓
┌──────────────────────┐
│   GPU Server         │
│  (ML Model)          │
│  - Image stickers    │
│  - Text stickers     │
└──────┬───────────────┘
       │
       ↓
┌──────────────────────┐
│   File Storage       │
│  - Sticker images    │
│  - Public URLs       │
└──────────────────────┘
```

### Components

1. **API Server**: Handles HTTP requests, file uploads, validation
2. **Redis**: Job queue and metadata storage
3. **Worker**: Background processor for ML tasks
4. **GPU Server**: External ML inference service (image + text models)
5. **File Storage**: Local or cloud storage for stickers

---

## 📦 Prerequisites

### Required
- **Node.js**: v18.0.0 or higher
- **Redis**: v6.0.0 or higher
- **npm**: v8.0.0 or higher

### Optional
- **GPU Server**: Your ML model server (for production)
- **PM2**: For process management (production)
- **Docker**: For containerized deployment

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd sticker-api
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Install Redis

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
```

**Windows:**
Download from [Redis Windows releases](https://github.com/microsoftarchive/redis/releases)

### 4. Verify Redis Installation

```bash
redis-cli ping
# Expected output: PONG
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Server Configuration
PORT=3000
NODE_ENV=development

# Upload Settings
UPLOAD_MAX_SIZE=10485760
ALLOWED_FILE_TYPES=image/jpeg,image/png,image/jpg,image/webp

# GPU Server Configuration
GPU_SERVER_URL=http://localhost:5000/api/generate-stickers
GPU_TEXT_SERVER_URL=http://localhost:5000/api/generate-text-stickers
GPU_TIMEOUT=60000
GPU_TEXT_TIMEOUT=30000

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Paths
UPLOAD_DIR=./uploads
TEMP_DIR=./temp

# Job Settings
MAX_JOB_RETRIES=3
JOB_TIMEOUT=300000
MAX_CONCURRENT_JOBS=5
```

---

## 🏃 Running the Application

### Development Mode

You need **4 terminal windows** running simultaneously:

**Terminal 1: Start Redis**
```bash
redis-server
```

**Terminal 2: Start Mock GPU Server** (for testing)
```bash
node mock-gpu-server.js
```

**Terminal 3: Start Worker**
```bash
npm run worker:dev
```

**Terminal 4: Start API Server**
```bash
npm run dev
```

### Production Mode

Using PM2 (recommended):

```bash
# Install PM2 globally
npm install -g pm2

# Start all services
pm2 start src/server.js --name sticker-api
pm2 start worker.js --name sticker-worker

# Check status
pm2 status

# View logs
pm2 logs

# Enable startup on boot
pm2 startup
pm2 save
```

---

## 📚 API Documentation

### Base URL
```
http://localhost:3000
```

---

## 🖼️ Image-Based Sticker Generation

### Upload Image

Upload an image file to generate stickers.

**Endpoint:** `POST /api/upload`

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `image` (file, required): Image file (JPEG, PNG, WEBP)

**Example using cURL:**
```bash
curl -X POST http://localhost:3000/api/upload \
  -F "image=@/path/to/your/image.jpg"
```

**Example using JavaScript:**
```javascript
const formData = new FormData();
formData.append('image', imageFile);

const response = await fetch('http://localhost:3000/api/upload', {
  method: 'POST',
  body: formData
});

const data = await response.json();
console.log(data.jobId);
```

**Example using Python:**
```python
import requests

with open('image.jpg', 'rb') as f:
    files = {'image': f}
    response = requests.post('http://localhost:3000/api/upload', files=files)

data = response.json()
job_id = data['data']['jobId']
```

**Success Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Job queued successfully",
  "data": {
    "jobId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "queued",
    "statusUrl": "/api/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "estimatedTime": "30-60 seconds"
  }
}
```

**Error Responses:**

*400 Bad Request - No file:*
```json
{
  "success": false,
  "error": "No image file provided"
}
```

*400 Bad Request - Invalid file type:*
```json
{
  "success": false,
  "error": "Invalid file type. Allowed types: image/jpeg, image/png, image/jpg, image/webp"
}
```

*413 Payload Too Large:*
```json
{
  "success": false,
  "error": "File too large",
  "maxSize": "10485760"
}
```

---

## 📝 Text-Based Sticker Generation

### Generate Text Stickers

Generate stickers from text or keywords.

**Endpoint:** `POST /api/generate-text`

**Request:**
- Method: `POST`
- Content-Type: `application/json`
- Body (one or both required):
  - `text` (string, optional): Text to generate stickers for (max 200 characters)
  - `keywords` (array, optional): Keywords for sticker generation (max 10 items)

**Example 1: Text Only**

```bash
curl -X POST http://localhost:3000/api/generate-text \
  -H "Content-Type: application/json" \
  -d '{"text": "Happy Birthday!"}'
```

**Example 2: Keywords Only**

```bash
curl -X POST http://localhost:3000/api/generate-text \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["happy", "birthday", "celebration"]}'
```

**Example 3: Both Text and Keywords**

```bash
curl -X POST http://localhost:3000/api/generate-text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Happy Birthday!",
    "keywords": ["party", "cake", "celebration"]
  }'
```

**Example using JavaScript:**
```javascript
const response = await fetch('http://localhost:3000/api/generate-text', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    text: "Happy Birthday!",
    keywords: ["party", "cake"]
  })
});

const data = await response.json();
console.log(data.jobId);
```

**Example using Python:**
```python
import requests

payload = {
    "text": "Happy Birthday!",
    "keywords": ["party", "cake", "celebration"]
}

response = requests.post(
    'http://localhost:3000/api/generate-text',
    json=payload
)

data = response.json()
job_id = data['data']['jobId']
```

**Success Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Text sticker job queued successfully",
  "data": {
    "jobId": "xyz-789",
    "status": "queued",
    "statusUrl": "/api/status/xyz-789",
    "estimatedTime": "15-30 seconds",
    "input": {
      "text": "Happy Birthday!",
      "keywords": ["party", "cake", "celebration"]
    }
  }
}
```

**Error Responses:**

*400 Bad Request - No input:*
```json
{
  "success": false,
  "error": "Either \"text\" or \"keywords\" field is required"
}
```

*400 Bad Request - Text too long:*
```json
{
  "success": false,
  "error": "Text must be 200 characters or less"
}
```

*400 Bad Request - Too many keywords:*
```json
{
  "success": false,
  "error": "Maximum 10 keywords allowed"
}
```

---

## 📊 Check Job Status

Get the current status and results of a job (works for both image and text jobs).

**Endpoint:** `GET /api/status/:jobId`

**Example:**
```bash
curl http://localhost:3000/api/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Response (Queued):**
```json
{
  "success": true,
  "jobId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "waiting",
  "progress": 0,
  "metadata": {
    "originalName": "vacation.jpg",
    "uploadedAt": "2024-02-09T10:30:00.000Z",
    "dimensions": {
      "width": 2000,
      "height": 1500,
      "format": "jpeg"
    }
  }
}
```

**Response (Processing):**
```json
{
  "success": true,
  "jobId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "active",
  "progress": 45,
  "metadata": {
    "originalName": "vacation.jpg",
    "uploadedAt": "2024-02-09T10:30:00.000Z"
  }
}
```

**Response (Completed - Image Job):**
```json
{
  "success": true,
  "jobId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "progress": 100,
  "stickers": [
    "http://localhost:3000/stickers/sticker-a1b2c3d4-1.png",
    "http://localhost:3000/stickers/sticker-a1b2c3d4-2.png",
    "http://localhost:3000/stickers/sticker-a1b2c3d4-3.png",
    "http://localhost:3000/stickers/sticker-a1b2c3d4-4.png",
    "http://localhost:3000/stickers/sticker-a1b2c3d4-5.png"
  ],
  "count": 5,
  "processingTime": "2.34s",
  "completedAt": "2024-02-09T10:30:15.000Z",
  "metadata": {
    "type": "image",
    "originalName": "vacation.jpg",
    "uploadedAt": "2024-02-09T10:30:00.000Z"
  }
}
```

**Response (Completed - Text Job):**
```json
{
  "success": true,
  "jobId": "xyz-789",
  "status": "completed",
  "progress": 100,
  "stickers": [
    "http://localhost:3000/stickers/text-sticker-xyz-789-1.png",
    "http://localhost:3000/stickers/text-sticker-xyz-789-2.png",
    "http://localhost:3000/stickers/text-sticker-xyz-789-3.png"
  ],
  "count": 3,
  "processingTime": "1.5s",
  "completedAt": "2024-02-09T10:30:15.000Z",
  "metadata": {
    "type": "text",
    "text": "Happy Birthday!",
    "keywords": ["party", "cake"],
    "createdAt": "2024-02-09T10:30:00.000Z"
  }
}
```

**Response (Failed):**
```json
{
  "success": true,
  "jobId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "failed",
  "progress": 40,
  "error": "GPU server timeout. Processing took too long.",
  "attempts": 3,
  "metadata": {
    "originalName": "vacation.jpg",
    "uploadedAt": "2024-02-09T10:30:00.000Z"
  }
}
```

**Error Response (404 Not Found):**
```json
{
  "success": false,
  "error": "Job not found"
}
```

---

## 📊 Get Queue Statistics

Get current queue statistics.

**Endpoint:** `GET /api/stats`

**Example:**
```bash
curl http://localhost:3000/api/stats
```

**Response:**
```json
{
  "success": true,
  "queue": {
    "waiting": 2,
    "active": 1,
    "completed": 150,
    "failed": 3,
    "delayed": 0,
    "total": 156
  },
  "timestamp": "2024-02-09T10:35:00.000Z"
}
```

---

## 🖼️ Download Sticker

Access a generated sticker image.

**Endpoint:** `GET /stickers/:filename`

**Example:**
```bash
# View in browser
http://localhost:3000/stickers/sticker-a1b2c3d4-1.png

# Download with cURL
curl -O http://localhost:3000/stickers/sticker-a1b2c3d4-1.png
```

**Response:**
- Content-Type: `image/png`
- Binary image data

---

## 📊 Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 202 | Accepted - Job queued successfully |
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource not found |
| 413 | Payload Too Large - File too big |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |
| 503 | Service Unavailable - GPU server down |

---

## 📁 Project Structure

```
sticker-api/
├── src/
│   ├── config/              # Configuration files
│   │   └── gpuConfig.js     # GPU server configuration
│   ├── controllers/         # Request handlers
│   │   └── imageController.js
│   ├── middleware/          # Request processing
│   │   ├── errorHandler.js
│   │   ├── rateLimiter.js
│   │   ├── uploadMiddleware.js
│   │   ├── validation.js
│   │   └── textValidation.js
│   ├── routes/              # API route definitions
│   │   └── imageRoutes.js
│   ├── services/            # External services
│   │   ├── gpuService.js
│   │   ├── textGpuService.js
│   │   ├── imageProcessor.js
│   │   ├── jobStorage.js
│   │   ├── queueService.js
│   │   └── storageService.js
│   ├── workers/             # Background processors
│   │   └── stickerWorker.js
│   └── server.js            # Main entry point
├── uploads/                 # Temporary uploads
│   └── stickers/           # Generated stickers
├── temp/                    # Temporary processing
├── .env                     # Environment config
├── .gitignore
├── package.json
├── worker.js               # Worker entry point
├── mock-gpu-server.js      # Mock GPU for testing
└── README.md
```

---

## 🔍 How It Works

### Complete Flow

**Image-Based Generation:**
```
1. User uploads image
2. API validates file (type, size, dimensions)
3. Job created with unique ID
4. Job added to Redis queue
5. API returns job ID (202 Accepted)
6. Worker picks up job from queue
7. Worker preprocesses image (resize to 512x512)
8. Worker converts to base64
9. Worker sends to GPU server
10. GPU generates 5 stickers
11. Worker receives base64 stickers
12. Worker converts to PNG files
13. Worker saves to disk
14. Worker stores URLs in Redis
15. Job marked as completed
16. User polls status endpoint
17. API returns sticker URLs
18. User downloads stickers
```

**Text-Based Generation:**
```
1. User sends text/keywords (JSON)
2. API validates input
3. Job created with unique ID
4. Job added to Redis queue
5. API returns job ID (202 Accepted)
6. Worker picks up job from queue
7. Worker sends text/keywords to GPU
8. GPU generates 3 text stickers
9. Worker receives base64 stickers
10. Worker converts to PNG files
11. Worker saves to disk
12. Worker stores URLs in Redis
13. Job marked as completed
14. User polls status endpoint
15. API returns sticker URLs
16. User downloads stickers
```

### Job States

```
created → waiting → active → completed
                          → failed → retry → active
```

**States:**
- `created`: Job just created
- `waiting`: In queue, waiting for worker
- `active`: Currently being processed
- `completed`: Successfully finished
- `failed`: Processing failed after retries

### Progress Tracking

**Image Jobs:**
- 0%: Job queued
- 10%: Preprocessing started
- 30%: Converted to base64
- 40%: Sent to GPU
- 70%: GPU completed, saving stickers
- 90%: Stickers saved, cleaning up
- 100%: Job completed

**Text Jobs:**
- 0%: Job queued
- 10%: Request validated
- 50%: GPU completed
- 90%: Stickers saved
- 100%: Job completed

---

## 🛠️ Development

### Available Scripts

```bash
# Start API server in development mode (auto-restart)
npm run dev

# Start worker in development mode (auto-restart)
npm run worker:dev

# Start API server in production mode
npm start

# Start worker in production mode
npm run worker
```

### Testing

**Manual Testing:**

```bash
# Test image upload
curl -X POST http://localhost:3000/api/upload \
  -F "image=@test-image.jpg"

# Test text generation
curl -X POST http://localhost:3000/api/generate-text \
  -H "Content-Type: application/json" \
  -d '{"text": "Happy Birthday!"}'

# Check status
curl http://localhost:3000/api/status/JOB_ID

# Queue stats
curl http://localhost:3000/api/stats
```

**Using Postman:**

Import the provided `Sticker-API.postman_collection.json` file:
1. Open Postman
2. Click "Import"
3. Select the JSON file
4. All requests ready to use

---

## 🚀 Production Deployment

### Using PM2

```bash
# Install PM2 globally
npm install -g pm2

# Start services
pm2 start src/server.js --name sticker-api
pm2 start worker.js --name sticker-worker

# Monitor
pm2 monit

# View logs
pm2 logs

# Restart
pm2 restart all

# Stop
pm2 stop all

# Enable auto-start on boot
pm2 startup
pm2 save
```

### Using Docker

**Build image:**
```bash
docker build -t sticker-api .
```

**Run with Docker Compose:**
```bash
docker-compose up -d
```

### Scaling

**Horizontal Scaling:**

```bash
# Scale workers
pm2 scale sticker-worker 5  # Run 5 worker instances

# Scale API servers (behind load balancer)
pm2 scale sticker-api 3     # Run 3 API instances
```

**Vertical Scaling:**
- Increase `MAX_CONCURRENT_JOBS` in `.env`
- Allocate more RAM to Redis
- Use faster storage (SSD)

---

## 🐛 Troubleshooting

### Redis Connection Error

**Error:**
```
Error: Redis connection to localhost:6379 failed
```

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
redis-server

# Check Redis logs
redis-cli info
```

---

### Upload Fails

**Error:**
```
{"success": false, "error": "No image file provided"}
```

**Solution:**
- Ensure `Content-Type: multipart/form-data`
- Field name must be `image`
- File must be JPEG, PNG, or WEBP

---

### Worker Not Processing Jobs

**Symptoms:**
- Jobs stuck in "waiting" state
- No logs in worker terminal

**Solution:**
```bash
# Check worker is running
ps aux | grep worker.js

# Restart worker
pm2 restart sticker-worker

# Check Redis queue
redis-cli
> KEYS *
> GET bull:sticker-generation:*
```

---

### GPU Server Timeout

**Error:**
```
{"status": "failed", "error": "GPU server timeout"}
```

**Solution:**
- Check GPU server is running
- Increase `GPU_TIMEOUT` in `.env`
- Check GPU server logs
- Verify network connectivity

---

### Out of Disk Space

**Error:**
```
ENOSPC: no space left on device
```

**Solution:**
```bash
# Check disk usage
df -h

# Clean up old stickers
rm -rf uploads/stickers/*

# Clean up temp files
rm -rf temp/*

# Clear Redis (careful!)
redis-cli FLUSHALL
```

---

## 🔒 Security Considerations

### Implemented

- ✅ File type validation
- ✅ File size limits
- ✅ Rate limiting
- ✅ Input sanitization
- ✅ Error message sanitization
- ✅ Helmet.js security headers
- ✅ CORS configuration

### Recommended for Production

- [ ] API authentication (API keys, JWT)
- [ ] User accounts and quotas
- [ ] Image content filtering
- [ ] Request signing
- [ ] HTTPS/TLS
- [ ] Firewall rules
- [ ] DDoS protection
- [ ] Audit logging

---


## 🙏 Acknowledgments

- Express.js team
- Bull queue library
- Sharp image processing
- Redis community



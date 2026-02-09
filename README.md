# 🎨 Sticker Generation API

A production-grade asynchronous image processing API that generates multiple sticker variations from uploaded images using GPU-powered ML models.

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
- [Contributing](#contributing)

---

## 🎯 Overview

This API accepts image uploads from users and generates multiple sticker variations using a GPU-powered machine learning model. The system uses an asynchronous architecture with job queues to handle long-running ML inference without blocking user requests.

### Key Capabilities

- ✅ Asynchronous image processing
- ✅ Real-time job progress tracking
- ✅ Automatic retry on failures
- ✅ Horizontally scalable architecture
- ✅ Production-ready error handling
- ✅ File validation and security


---

## ✨ Features

### User Features
- Upload images via REST API
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
- **Validation**: Image format, size, and dimension checks
- **Logging**: Comprehensive request and error logging
- **Scalability**: Add more workers for parallel processing

---

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP POST (multipart/form-data)
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
│  - Generate stickers │
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
4. **GPU Server**: External ML inference service
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
GPU_TIMEOUT=60000

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

### Configuration Details

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | API server port | 3000 |
| `UPLOAD_MAX_SIZE` | Max file size in bytes | 10485760 (10MB) |
| `ALLOWED_FILE_TYPES` | Comma-separated MIME types | image/jpeg,image/png,image/jpg,image/webp |
| `GPU_SERVER_URL` | GPU server endpoint | http://localhost:5000/api/generate-stickers |
| `GPU_TIMEOUT` | GPU request timeout (ms) | 60000 (60 seconds) |
| `REDIS_HOST` | Redis server host | localhost |
| `REDIS_PORT` | Redis server port | 6379 |
| `MAX_JOB_RETRIES` | Retry attempts on failure | 3 |
| `JOB_TIMEOUT` | Max job processing time (ms) | 300000 (5 minutes) |
| `MAX_CONCURRENT_JOBS` | Parallel worker jobs | 5 |

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

### Endpoints

---

#### 1. Upload Image

Upload an image for sticker generation.

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
console.log(data.jobId); // Use this to check status
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

*400 Bad Request:*
```json
{
  "success": false,
  "error": "No image file provided"
}
```

*400 Bad Request (Invalid file type):*
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

#### 2. Check Job Status

Get the current status and results of a job.

**Endpoint:** `GET /api/status/:jobId`

**Parameters:**
- `jobId` (path parameter): Job ID from upload response

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

**Response (Completed):**
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
    "originalName": "vacation.jpg",
    "uploadedAt": "2024-02-09T10:30:00.000Z"
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

#### 3. Get Queue Statistics

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

#### 4. Health Check

Check if the API is running.

**Endpoint:** `GET /health`

**Example:**
```bash
curl http://localhost:3000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-02-09T10:35:00.000Z",
  "uptime": 3600.5
}
```

---

#### 5. Download Sticker

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

### Status Codes

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
│   ├── controllers/         # Request handlers (business logic)
│   │   └── imageController.js
│   ├── middleware/          # Request processing middleware
│   │   ├── errorHandler.js  # Global error handler
│   │   ├── uploadMiddleware.js  # File upload handling
│   │   └── validation.js    # Input validation
│   ├── routes/              # API route definitions
│   │   └── imageRoutes.js
│   ├── services/            # External service interactions
│   │   ├── gpuService.js    # GPU server communication
│   │   ├── imageProcessor.js  # Image manipulation
│   │   ├── jobStorage.js    # Job metadata storage
│   │   ├── queueService.js  # Queue management
│   │   └── storageService.js  # File storage
│   ├── workers/             # Background job processors
│   │   └── stickerWorker.js
│   └── server.js            # Main application entry point
├── uploads/                 # Temporary uploaded files
│   └── stickers/           # Generated sticker files
├── temp/                    # Temporary processing files
├── .env                     # Environment variables (not in git)
├── .gitignore              # Git ignore rules
├── package.json            # Dependencies and scripts
├── worker.js               # Worker process entry point
├── mock-gpu-server.js      # Mock GPU server for testing
└── README.md               # This file
```

### File Descriptions

#### `/src/server.js`
Main application entry point. Sets up Express server, middleware, routes, and error handling.

#### `/src/routes/imageRoutes.js`
Defines API endpoints and connects them to controller functions with middleware chain.

#### `/src/controllers/imageController.js`
Business logic for handling requests. Coordinates between services to process uploads and check status.

#### `/src/middleware/uploadMiddleware.js`
Handles file uploads using Multer. Configures storage, file filtering, and size limits.

#### `/src/middleware/validation.js`
Validates uploaded images using Sharp. Checks dimensions, format, and file integrity.

#### `/src/middleware/errorHandler.js`
Global error handler. Catches all errors and returns user-friendly messages.

#### `/src/middleware/rateLimiter.js`
Rate limiting middleware. Protects API from abuse with configurable limits.

#### `/src/services/imageProcessor.js`
Image manipulation service. Handles resizing, format conversion, base64 encoding/decoding.

#### `/src/services/gpuService.js`
GPU server communication. Sends images to ML model and receives generated stickers.

#### `/src/services/queueService.js`
Job queue management using Bull. Handles job creation, status tracking, and statistics.

#### `/src/services/jobStorage.js`
Stores job metadata and sticker URLs in Redis. Provides fast access to job information.

#### `/src/services/storageService.js`
File storage service. Saves stickers to disk and generates public URLs.

#### `/src/workers/stickerWorker.js`
Background worker process. Processes jobs from queue, handles ML inference, saves results.

#### `/worker.js`
Worker process entry point. Starts the worker and handles graceful shutdown.

#### `/mock-gpu-server.js`
Mock GPU server for testing. Simulates ML model responses without real GPU.

---

## 🔍 How It Works

### Complete Request Flow

```
1. User uploads image
   ↓
2. API receives file
   ↓
3. Middleware validates file
   ↓
4. Controller creates job
   ↓
5. Job added to Redis queue
   ↓
6. API returns job ID (202 Accepted)
   ↓
7. Worker picks up job from queue
   ↓
8. Worker preprocesses image
   ↓
9. Worker sends to GPU server
   ↓
10. GPU generates stickers
    ↓
11. Worker saves stickers to disk
    ↓
12. Worker stores URLs in Redis
    ↓
13. Job marked as completed
    ↓
14. User polls status endpoint
    ↓
15. API returns sticker URLs
    ↓
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

Progress is updated at key milestones:

- **0%**: Job queued
- **10%**: Image preprocessing started
- **30%**: Converted to base64
- **40%**: Sent to GPU
- **70%**: GPU completed, saving stickers
- **90%**: Stickers saved, cleaning up
- **100%**: Job completed

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

### Adding New Features

1. **Add new endpoint:**
   - Define route in `src/routes/imageRoutes.js`
   - Add controller function in `src/controllers/imageController.js`
   - Add validation if needed in `src/middleware/validation.js`

2. **Add new service:**
   - Create new file in `src/services/`
   - Export service instance
   - Import and use in controllers/workers

3. **Modify job processing:**
   - Edit `src/workers/stickerWorker.js`
   - Update progress tracking as needed
   - Test with mock GPU server first

### Testing

**Manual Testing:**

```bash
# Upload test
curl -X POST http://localhost:3000/api/upload \
  -F "image=@test-image.jpg"

# Status check
curl http://localhost:3000/api/status/JOB_ID

# Queue stats
curl http://localhost:3000/api/stats

# Health check
curl http://localhost:3000/health
```

**Load Testing (using Apache Bench):**

```bash
# Install Apache Bench (if needed)
sudo apt install apache2-utils  # Ubuntu
brew install httpd              # macOS

# Test concurrent uploads
ab -n 100 -c 10 -p test-image.jpg \
   -T "multipart/form-data" \
   http://localhost:3000/api/upload
```

---

## 🚀 Production Deployment

### Using PM2

```bash
# Install PM2 globally
npm install -g pm2

# Start services
pm2 start ecosystem.config.js

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

### Environment Considerations

**Development:**
- Use mock GPU server
- Enable detailed logging
- Single worker instance

**Production:**
- Connect to real GPU server
- Disable mock GPU server
- Multiple worker instances
- Use managed Redis (AWS ElastiCache, etc.)
- Use cloud storage (S3, GCS)
- Enable monitoring (Sentry, DataDog)
- Configure SSL/TLS
- Set up load balancer

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

### Common Issues

#### Redis Connection Error

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

#### Upload Fails

**Error:**
```
{"success": false, "error": "No image file provided"}
```

**Solution:**
- Ensure `Content-Type: multipart/form-data`
- Field name must be `image`
- File must be JPEG, PNG, or WEBP

#### Worker Not Processing Jobs

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

#### GPU Server Timeout

**Error:**
```
{"status": "failed", "error": "GPU server timeout"}
```

**Solution:**
- Check GPU server is running
- Increase `GPU_TIMEOUT` in `.env`
- Check GPU server logs
- Verify network connectivity

#### Out of Disk Space

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

#### High Memory Usage

**Solution:**
```bash
# Monitor memory
pm2 monit

# Reduce concurrent jobs
# Edit .env:
MAX_CONCURRENT_JOBS=2

# Restart worker
pm2 restart sticker-worker

# Enable automatic cleanup in worker
# (already implemented in imageProcessor.cleanup)
```

---

## 📊 Monitoring

### Logs

**API Server logs:**
```bash
pm2 logs sticker-api
```

**Worker logs:**
```bash
pm2 logs sticker-worker
```

**Redis logs:**
```bash
redis-cli
> MONITOR
```

### Metrics to Track

- Request rate (requests/second)
- Response time (milliseconds)
- Queue depth (jobs waiting)
- Processing time (seconds per job)
- Success rate (%)
- Error rate (%)
- Disk usage (MB/GB)
- Memory usage (MB/GB)

### Health Checks

```bash
# API health
curl http://localhost:3000/health

# Queue stats
curl http://localhost:3000/api/stats

# Redis health
redis-cli ping
```

---

## 🔒 Security Considerations

### Implemented

- ✅ File type validation
- ✅ File size limits
- ✅ Input sanitization
- ✅ Error message sanitization
- ✅ Helmet.js security headers
- ✅ CORS configuration

### Recommended for Production

- [ ] API authentication (API keys, JWT)
- [ ] User accounts and quotas
- [ ] Image content filtering (NSFW detection)
- [ ] Request signing
- [ ] HTTPS/TLS
- [ ] Firewall rules
- [ ] DDoS protection
- [ ] Audit logging


## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make changes
5. Test thoroughly
6. Submit pull request

### Code Style

- Use ES6+ features
- Follow existing patterns
- Add comments for complex logic
- Update README for new features

### Commit Messages

```
feat: Add batch upload support
fix: Resolve Redis connection issue
docs: Update API documentation
refactor: Simplify image preprocessing
```
## 🙏 Acknowledgments

- Express.js team
- Bull queue library
- Sharp image processing
- Redis community


const express = require('express');
const app = express();

app.use(express.json({ limit: '50mb' }));

// Mock GPU endpoint
app.post('/api/generate-stickers', (req, res) => {
  console.log(' Mock GPU received request');
  

  // Simulate processing time
  setTimeout(() => {
    // Generate mock stickers (1x1 pixel transparent PNG in base64)
    const mockStickerBase64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
    
    const stickers = [];
    for (let i = 0; i < 5; i++) {
      stickers.push({
        id: i + 1,
        image: mockStickerBase64
      });
    }

    res.json({
      success: true,
      stickers: stickers,
      message: 'Stickers generated (mock)'
    });
  }, 2000); // 2 second delay to simulate GPU processing
});


const PORT = 5000;
app.listen(PORT, () => {
  console.log(` Mock GPU server running on http://localhost:${PORT}`);
});

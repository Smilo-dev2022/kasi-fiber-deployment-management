require('dotenv').config();
const path = require('path');
const connectDB = require('./config/database');
const { buildApp } = require('./serverApp');
const { registerJobs } = require('./jobs/scheduler');

// Connect Database
connectDB();

// Build the app
const app = buildApp();

// Serve static assets in production
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, '../client/build')));
  app.get('*', (req, res) => {
    res.sendFile(path.resolve(__dirname, '../client', 'build', 'index.html'));
  });
}

const PORT = process.env.PORT || 5000;
if (require.main === module) {
  app.listen(PORT, () => console.log(`Server started on port ${PORT}`));
  // Start background jobs only when running the server
  registerJobs();
}

module.exports = app;
const mongoose = require('mongoose');
let memoryServer = null;

const connectDB = async () => {
  try {
    let uri = process.env.MONGODB_URI || 'mongodb://localhost:27017/kasi_fiber_db';
    if (process.env.USE_MEMORY_MONGO === 'true') {
      if (!process.env.MONGO_MEMORY_URI) {
        // Start a dedicated in-memory MongoDB instance
        const { MongoMemoryServer } = require('mongodb-memory-server');
        memoryServer = await MongoMemoryServer.create();
        uri = memoryServer.getUri();
        process.env.MONGO_MEMORY_URI = uri;
      } else {
        uri = process.env.MONGO_MEMORY_URI;
      }
    }
    const conn = await mongoose.connect(uri, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
    });

    console.log(`MongoDB Connected: ${conn.connection.host}`);
  } catch (error) {
    console.error('Database connection error:', error.message);
    // Don't exit process in development
    if (process.env.NODE_ENV === 'production') {
      process.exit(1);
    }
  }
};

module.exports = connectDB;
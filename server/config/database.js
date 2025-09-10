const mongoose = require('mongoose');
let memoryServer = null;

const connectDB = async () => {
  const uri = process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/kasi_fiber_db';
  try {
    const conn = await mongoose.connect(uri, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
    });
    console.log(`MongoDB Connected: ${conn.connection.host}`);
  } catch (error) {
    console.error('Database connection error:', error.message);
    const useMemory = (process.env.USE_MEMORY_DB || 'true') === 'true' && process.env.NODE_ENV !== 'production';
    if (useMemory) {
      try {
        const { MongoMemoryServer } = require('mongodb-memory-server');
        memoryServer = await MongoMemoryServer.create();
        const memUri = memoryServer.getUri('kasi_fiber_db');
        const conn = await mongoose.connect(memUri, {
          useNewUrlParser: true,
          useUnifiedTopology: true,
        });
        console.log(`MongoMemoryServer Connected: ${conn.connection.host}`);
      } catch (memErr) {
        console.error('Failed to start in-memory MongoDB:', memErr.message);
        if (process.env.NODE_ENV === 'production') {
          process.exit(1);
        }
      }
    } else if (process.env.NODE_ENV === 'production') {
      process.exit(1);
    }
  }
};

module.exports = connectDB;
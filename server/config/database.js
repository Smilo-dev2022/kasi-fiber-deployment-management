const mongoose = require('mongoose');
let memoryServer = null;

const connectDB = async () => {
  try {
    const conn = await mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/kasi_fiber_db', {
      useNewUrlParser: true,
      useUnifiedTopology: true,
      serverSelectionTimeoutMS: 2000
    });
    console.log(`MongoDB Connected: ${conn.connection.host}`);
    return conn;
  } catch (error) {
    console.error('Database connection error:', error.message);
    if (process.env.NODE_ENV === 'production') {
      process.exit(1);
    }
    // Development fallback: spin up in-memory Mongo for smoke tests
    try {
      const { MongoMemoryServer } = require('mongodb-memory-server');
      memoryServer = await MongoMemoryServer.create();
      const uri = memoryServer.getUri();
      const conn = await mongoose.connect(uri, {
        useNewUrlParser: true,
        useUnifiedTopology: true
      });
      console.log(`Mongo Memory Server started at ${uri}`);
      return conn;
    } catch (memErr) {
      console.error('Failed to start Mongo Memory Server:', memErr.message);
    }
  }
};

process.on('SIGINT', async () => {
  try {
    await mongoose.disconnect();
    if (memoryServer) {
      await memoryServer.stop();
    }
  } finally {
    process.exit(0);
  }
});

module.exports = connectDB;
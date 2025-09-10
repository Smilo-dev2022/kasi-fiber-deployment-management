process.env.NODE_ENV = 'test';
process.env.JWT_SECRETS = 'testsecret';
process.env.CORS_ALLOWLIST = '';

const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');
jest.setTimeout(30000);

let mongo;

beforeAll(async () => {
  mongo = await MongoMemoryServer.create();
  const uri = mongo.getUri('kasi_fiber_test');
  process.env.MONGODB_URI = uri;
  await mongoose.connect(uri, { useNewUrlParser: true, useUnifiedTopology: true });
});

afterAll(async () => {
  if (mongoose.connection.readyState === 1) {
    await mongoose.connection.dropDatabase();
    await mongoose.connection.close();
  }
  if (mongo) {
    await mongo.stop();
  }
});


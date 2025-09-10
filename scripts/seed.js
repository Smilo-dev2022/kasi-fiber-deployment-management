/* eslint-disable no-console */
require('dotenv').config();
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const User = require('../server/models/User');

async function run() {
  // Try .env, else attach to the same connection used by the app (memory fallback)
  if (mongoose.connection.readyState !== 1) {
    const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/kasi_fiber_db';
    try {
      await mongoose.connect(mongoUri, { serverSelectionTimeoutMS: 1000 });
    } catch (e) {
      const { MongoMemoryServer } = require('mongodb-memory-server');
      const mem = await MongoMemoryServer.create();
      await mongoose.connect(mem.getUri());
    }
  }
  console.log('Connected to Mongo');

  const ensureUser = async ({ name, email, password, role, phone }) => {
    let user = await User.findOne({ email });
    if (user) {
      console.log(`User exists: ${email}`);
      return user;
    }
    const hashed = await bcrypt.hash(password, 10);
    user = await User.create({ name, email, password: hashed, role, phone, isActive: true });
    console.log(`Created user: ${email} (${role})`);
    return user;
  };

  await ensureUser({ name: 'Admin', email: 'admin@example.com', password: 'Admin123!', role: 'admin' });
  await ensureUser({ name: 'Project Manager', email: 'pm@example.com', password: 'Pm123456', role: 'project_manager' });
  await ensureUser({ name: 'Site Manager', email: 'smme@example.com', password: 'Smme1234', role: 'site_manager' });

  await mongoose.disconnect();
  console.log('Seed complete');
}

run().catch((e) => {
  console.error(e);
  process.exit(1);
});


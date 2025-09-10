/* eslint-disable no-console */
require('dotenv').config();
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const User = require('../server/models/User');

async function main() {
  const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017/kasi_fiber_db';
  await mongoose.connect(uri, { useNewUrlParser: true, useUnifiedTopology: true });

  const users = [
    { name: 'Admin', email: 'admin@example.com', password: 'Admin123!', role: 'admin' },
    { name: 'Project Manager', email: 'pm@example.com', password: 'Pm123456', role: 'project_manager' },
    { name: 'Site Manager', email: 'smme@example.com', password: 'Smme1234', role: 'site_manager' }
  ];

  for (const u of users) {
    const existing = await User.findOne({ email: u.email });
    if (existing) {
      console.log(`User exists: ${u.email}`);
      continue;
    }
    const user = new User(u);
    await user.save();
    console.log(`Created: ${u.email}`);
  }

  await mongoose.disconnect();
  console.log('Seeding complete');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});


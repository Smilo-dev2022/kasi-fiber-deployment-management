/* eslint-disable no-console */
require('dotenv').config();
const connectDB = require('../config/database');
const User = require('../models/User');

async function main() {
  await connectDB();

  const email = process.env.SEED_USER_EMAIL || 'test@example.com';
  const password = process.env.SEED_USER_PASSWORD || 'Passw0rd!';
  const name = process.env.SEED_USER_NAME || 'Test User';
  const role = process.env.SEED_USER_ROLE || 'project_manager';
  const phone = process.env.SEED_USER_PHONE || '';

  const existing = await User.findOne({ email });
  if (existing) {
    console.log(`Seed user already exists: ${email}`);
    process.exit(0);
    return;
  }

  const user = new User({ name, email, password, role, phone });
  await user.save();

  console.log('Seed user created:', { email, role });
  process.exit(0);
}

main().catch((err) => {
  console.error('Failed to seed user:', err);
  process.exit(1);
});


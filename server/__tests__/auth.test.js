const request = require('supertest');
const mongoose = require('mongoose');
require('../tests/setup');

const { buildApp } = require('../serverApp');
const app = buildApp();
const User = require('../models/User');

describe('Auth routes', () => {
  test('register and login', async () => {
    const register = await request(app)
      .post('/api/auth/register')
      .send({ name: 'Alice', email: 'alice@example.com', password: 'password', role: 'project_manager' })
      .expect(200);
    expect(register.body.token).toBeTruthy();

    const login = await request(app)
      .post('/api/auth/login')
      .send({ email: 'alice@example.com', password: 'password' })
      .expect(200);
    expect(login.body.token).toBeTruthy();

    const me = await request(app)
      .get('/api/auth/user')
      .set('Authorization', `Bearer ${login.body.token}`)
      .expect(200);
    expect(me.body.email).toBe('alice@example.com');
  });
});


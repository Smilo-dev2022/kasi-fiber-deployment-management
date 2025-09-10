const request = require('supertest');
require('../tests/setup');
const { buildApp } = require('../serverApp');
const app = buildApp();

describe('Users and Reports', () => {
  let adminToken;
  beforeAll(async () => {
    const admin = await request(app).post('/api/auth/register').send({ name: 'Admin', email: 'adminu@example.com', password: 'password', role: 'admin' });
    adminToken = admin.body.token;
  });

  test('users list requires admin/PM', async () => {
    const login = await request(app).post('/api/auth/login').send({ email: 'adminu@example.com', password: 'password' }).expect(200);
    const token = login.body.token;
    const res = await request(app).get('/api/users').set('Authorization', `Bearer ${token}`).expect(200);
    expect(Array.isArray(res.body)).toBe(true);
  });

  test('dashboard reports require auth', async () => {
    const login = await request(app).post('/api/auth/login').send({ email: 'adminu@example.com', password: 'password' }).expect(200);
    const token = login.body.token;
    await request(app).get('/api/reports/dashboard').set('Authorization', `Bearer ${token}`).expect(200);
  });
});


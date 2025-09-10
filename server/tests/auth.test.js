const request = require('supertest');
require('./setup');
const app = require('../index');
const User = require('../models/User');

describe('Auth routes', () => {
  beforeAll(async () => {
    await User.deleteMany({});
  });

  test('register and login', async () => {
    const registerRes = await request(app)
      .post('/api/auth/register')
      .send({ name: 'Test', email: 'test@example.com', password: 'secret12', role: 'admin' })
      .expect(200);
    expect(registerRes.body.token).toBeDefined();

    const loginRes = await request(app)
      .post('/api/auth/login')
      .send({ email: 'test@example.com', password: 'secret12' })
      .expect(200);
    expect(loginRes.body.token).toBeDefined();

    const meRes = await request(app)
      .get('/api/auth/user')
      .set('Authorization', `Bearer ${loginRes.body.token}`)
      .expect(200);
    expect(meRes.body.email).toBe('test@example.com');
  });
});


const request = require('supertest');
require('./setup');
const app = require('../index');

let adminToken;

beforeAll(async () => {
  const res = await request(app).post('/api/auth/register').send({
    name: 'Admin', email: 'admin2@example.com', password: 'secret12', role: 'admin'
  });
  adminToken = res.body.token;
});

describe('Settings routes', () => {
  test('upsert SLA map and fetch', async () => {
    await request(app)
      .put('/api/settings/sla')
      .set('Authorization', `Bearer ${adminToken}`)
      .send({ map: { installation: 72, testing: 48 } })
      .expect(200);

    const list = await request(app)
      .get('/api/settings')
      .set('Authorization', `Bearer ${adminToken}`)
      .expect(200);
    expect(Array.isArray(list.body)).toBe(true);
  });
});


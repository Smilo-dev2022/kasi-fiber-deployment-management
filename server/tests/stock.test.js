const request = require('supertest');
require('./setup');
const app = require('../index');
const User = require('../models/User');
const Asset = require('../models/Asset');

let adminToken;

beforeAll(async () => {
  await User.deleteMany({});
  await Asset.deleteMany({});
  const admin = await request(app).post('/api/auth/register').send({
    name: 'Admin', email: 'admin@example.com', password: 'secret12', role: 'admin'
  });
  adminToken = admin.body.token;
});

describe('Assets/Stock', () => {
  test('create asset and issue/install flow', async () => {
    const created = await request(app)
      .post('/api/stock')
      .set('Authorization', `Bearer ${adminToken}`)
      .send({ code: 'A001', type: 'ONT' })
      .expect(200);
    expect(created.body.code).toBe('A001');

    const issue = await request(app)
      .post('/api/stock/A001/scan')
      .set('Authorization', `Bearer ${adminToken}`)
      .send({ action: 'ISSUE' })
      .expect(200);
    expect(issue.body.status).toBe('Issued');

    const install = await request(app)
      .post('/api/stock/A001/scan')
      .set('Authorization', `Bearer ${adminToken}`)
      .send({ action: 'INSTALL' })
      .expect(200);
    expect(install.body.status).toBe('Installed');
  });
});


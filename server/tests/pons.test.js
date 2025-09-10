const request = require('supertest');
require('./setup');
const app = require('../index');
const User = require('../models/User');
const PON = require('../models/PON');

let pmToken;

beforeAll(async () => {
  await User.deleteMany({});
  await PON.deleteMany({});

  const pm = await request(app).post('/api/auth/register').send({
    name: 'PM', email: 'pm@example.com', password: 'secret12', role: 'project_manager'
  });
  pmToken = pm.body.token;
});

describe('PON routes', () => {
  test('create, get, update, progress', async () => {
    const create = await request(app)
      .post('/api/pons')
      .set('Authorization', `Bearer ${pmToken}`)
      .send({
        ponId: 'P001',
        name: 'PON 1',
        location: 'Ward X',
        coordinates: { latitude: -26.2, longitude: 28.04 },
        startDate: '2024-01-01',
        expectedEndDate: '2024-12-31',
        fiberCount: 12,
        ward: 'Ward-1'
      })
      .expect(200);
    const ponId = create.body._id;

    const list = await request(app)
      .get('/api/pons')
      .set('Authorization', `Bearer ${pmToken}`)
      .expect(200);
    expect(list.body.length).toBeGreaterThan(0);

    const getOne = await request(app)
      .get(`/api/pons/${ponId}`)
      .set('Authorization', `Bearer ${pmToken}`)
      .expect(200);
    expect(getOne.body.pon._id).toBe(ponId);

    const updated = await request(app)
      .put(`/api/pons/${ponId}`)
      .set('Authorization', `Bearer ${pmToken}`)
      .send({ notes: 'updated' })
      .expect(200);
    expect(updated.body.notes).toBe('updated');

    await request(app)
      .put(`/api/pons/${ponId}/progress`)
      .set('Authorization', `Bearer ${pmToken}`)
      .expect(200);
  });
});


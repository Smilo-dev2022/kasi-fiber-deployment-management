const request = require('supertest');
require('./setup');
const app = require('../index');
const User = require('../models/User');
const PON = require('../models/PON');
const Task = require('../models/Task');

let pmToken, smToken, ponId, taskId;

beforeAll(async () => {
  await User.deleteMany({});
  await PON.deleteMany({});
  await Task.deleteMany({});
  const pm = await request(app).post('/api/auth/register').send({
    name: 'PM', email: 'pm2@example.com', password: 'secret12', role: 'project_manager'
  });
  pmToken = pm.body.token;
  const sm = await request(app).post('/api/auth/register').send({
    name: 'SM', email: 'sm2@example.com', password: 'secret12', role: 'site_manager'
  });
  smToken = sm.body.token;

  const pon = await request(app)
    .post('/api/pons')
    .set('Authorization', `Bearer ${pmToken}`)
    .send({
      ponId: 'P002',
      name: 'PON 2',
      location: 'Ward Y',
      coordinates: { latitude: -26.1, longitude: 28.05 },
      startDate: '2024-01-01',
      expectedEndDate: '2024-12-31',
      fiberCount: 12,
      ward: 'Ward-2'
    });
  ponId = pon.body._id;
});

describe('Task routes', () => {
  test('create, list, update status', async () => {
    const smUser = await request(app).get('/api/auth/user').set('Authorization', `Bearer ${smToken}`);

    const create = await request(app)
      .post('/api/tasks')
      .set('Authorization', `Bearer ${pmToken}`)
      .send({
        title: 'Install cable',
        type: 'installation',
        pon: ponId,
        assignedTo: smUser.body._id,
        dueDate: '2024-02-01'
      })
      .expect(200);
    taskId = create.body._id;

    const list = await request(app)
      .get('/api/tasks')
      .set('Authorization', `Bearer ${pmToken}`)
      .expect(200);
    expect(list.body.length).toBeGreaterThan(0);

    const status = await request(app)
      .put(`/api/tasks/${taskId}/status`)
      .set('Authorization', `Bearer ${pmToken}`)
      .send({ status: 'in_progress' })
      .expect(200);
    expect(status.body.status).toBe('in_progress');
  });
});


const request = require('supertest');
const fs = require('fs');
const path = require('path');
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
    name: 'PM', email: 'pm3@example.com', password: 'secret12', role: 'project_manager'
  });
  pmToken = pm.body.token;
  const sm = await request(app).post('/api/auth/register').send({
    name: 'SM', email: 'sm3@example.com', password: 'secret12', role: 'site_manager'
  });
  smToken = sm.body.token;

  const pon = await request(app)
    .post('/api/pons')
    .set('Authorization', `Bearer ${pmToken}`)
    .send({
      ponId: 'P003',
      name: 'PON 3',
      location: 'Ward Z',
      coordinates: { latitude: -26.0, longitude: 28.06 },
      startDate: '2024-01-01',
      expectedEndDate: '2024-12-31',
      fiberCount: 12,
      ward: 'Ward-3'
    });
  ponId = pon.body._id;

  const smUser = await request(app).get('/api/auth/user').set('Authorization', `Bearer ${smToken}`);
  const task = await request(app)
    .post('/api/tasks')
    .set('Authorization', `Bearer ${pmToken}`)
    .send({
      title: 'Stringing',
      type: 'stringing',
      pon: ponId,
      assignedTo: smUser.body._id,
      dueDate: '2024-02-01',
      evidenceRequired: true
    });
  taskId = task.body._id;
});

describe('Photo uploads', () => {
  test('reject non-allowed file type', async () => {
    const dummyPath = path.join(__dirname, 'dummy.txt');
    fs.writeFileSync(dummyPath, 'hello');
    await request(app)
      .post(`/api/photos/upload/${taskId}`)
      .set('Authorization', `Bearer ${pmToken}`)
      .attach('photo', dummyPath)
      .expect(500); // multer will throw
    fs.unlinkSync(dummyPath);
  });
});


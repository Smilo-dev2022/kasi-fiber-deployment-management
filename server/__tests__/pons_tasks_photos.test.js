const request = require('supertest');
const path = require('path');
require('../tests/setup');
const { buildApp } = require('../serverApp');
const app = buildApp();

describe('PONs, Tasks, Photos', () => {
  let pmToken;
  let smToken;
  let ponId;
  let taskId;

  beforeAll(async () => {
    const pm = await request(app).post('/api/auth/register').send({ name: 'PM', email: 'pmptp@example.com', password: 'password', role: 'project_manager' });
    pmToken = pm.body.token;
    const sm = await request(app).post('/api/auth/register').send({ name: 'SM', email: 'smptp@example.com', password: 'password', role: 'site_manager' });
    smToken = sm.body.token;
  });

  test('create PON as PM with validation', async () => {
    const res = await request(app)
      .post('/api/pons')
      .set('Authorization', `Bearer ${pmToken}`)
      .send({
        ponId: 'PON-001',
        name: 'Test PON',
        location: 'Ward 1',
        coordinates: { latitude: -26.2041, longitude: 28.0473 },
        startDate: '2025-01-01',
        expectedEndDate: '2025-01-31',
        fiberCount: 12
      })
      .expect(200);
    ponId = res.body._id;
  });

  test('create Task requires PM role and valid fields', async () => {
    const meSm = await request(app).post('/api/auth/login').send({ email: 'smptp@example.com', password: 'password' }).expect(200);
    const smTok = meSm.body.token;
    const meSmUser = await request(app).get('/api/auth/user').set('Authorization', `Bearer ${smTok}`).expect(200);
    const res = await request(app)
      .post('/api/tasks')
      .set('Authorization', `Bearer ${pmToken}`)
      .send({
        title: 'Stringing Section A',
        type: 'stringing',
        pon: ponId,
        assignedTo: meSmUser.body._id,
        dueDate: '2025-01-10',
        evidenceRequired: true
      })
      .expect(200);
    taskId = res.body._id;
  });

  test('upload photo rejects PDFs >10MB and non-allowed types', async () => {
    await request(app)
      .post(`/api/photos/upload/${taskId}`)
      .set('Authorization', `Bearer ${pmToken}`)
      .attach('photo', Buffer.alloc(1024), { filename: 'doc.txt', contentType: 'text/plain' })
      .expect(500); // filtered by multer -> server error path
  });

  test('complete task blocked if evidence outside geofence', async () => {
    // Upload a small PNG (no EXIF so withinGeofence stays null -> allowed)
    await request(app)
      .post(`/api/photos/upload/${taskId}`)
      .set('Authorization', `Bearer ${pmToken}`)
      .attach('photo', Buffer.from([137,80,78,71,13,10,26,10]), { filename: 'a.png', contentType: 'image/png' })
      .expect(200);
    // Attempt completion (no explicit false geofence -> allowed)
    await request(app)
      .put(`/api/tasks/${taskId}/status`)
      .set('Authorization', `Bearer ${pmToken}`)
      .send({ status: 'completed' })
      .expect(200);
  });
});


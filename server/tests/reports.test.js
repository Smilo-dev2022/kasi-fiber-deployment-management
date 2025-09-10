const request = require('supertest');
require('./setup');
const app = require('../index');

test('reports dashboard responds for PM', async () => {
  const pm = await request(app).post('/api/auth/register').send({
    name: 'PM', email: 'rep@example.com', password: 'secret12', role: 'project_manager'
  });
  const token = pm.body.token;
  const res = await request(app)
    .get('/api/reports/dashboard')
    .set('Authorization', `Bearer ${token}`)
    .expect(200);
  expect(res.body).toHaveProperty('pons');
  expect(res.body).toHaveProperty('tasks');
});


const request = require('supertest');
const app = require('../../src/app');
const store = require('../../src/store');

beforeEach(() => store.clear());

describe('GET /accounts/:accountId/balance', () => {
  test('returns zero balance for account with no transactions', async () => {
    const res = await request(app).get('/accounts/ACC-12345/balance');
    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ accountId: 'ACC-12345', balance: 0, currency: 'USD' });
  });

  test('increases balance on deposit', async () => {
    await request(app).post('/transactions').send({ toAccount: 'ACC-00001', amount: 500, currency: 'USD', type: 'deposit' });
    const res = await request(app).get('/accounts/ACC-00001/balance');
    expect(res.body.balance).toBe(500);
  });

  test('decreases balance on withdrawal', async () => {
    await request(app).post('/transactions').send({ toAccount: 'ACC-00001', amount: 500, currency: 'USD', type: 'deposit' });
    await request(app).post('/transactions').send({ fromAccount: 'ACC-00001', amount: 200, currency: 'USD', type: 'withdrawal' });
    const res = await request(app).get('/accounts/ACC-00001/balance');
    expect(res.body.balance).toBeCloseTo(300);
  });

  test('returns 400 for invalid account format', async () => {
    const res = await request(app).get('/accounts/INVALID/balance');
    expect(res.status).toBe(400);
  });
});

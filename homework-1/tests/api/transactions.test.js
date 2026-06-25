const request = require('supertest');
const app = require('../../src/app');
const store = require('../../src/store');

beforeEach(() => store.clear());

describe('POST /transactions', () => {
  const validTransfer = {
    fromAccount: 'ACC-12345',
    toAccount: 'ACC-67890',
    amount: 100.50,
    currency: 'USD',
    type: 'transfer',
  };

  test('creates transaction and returns 201', async () => {
    const res = await request(app).post('/transactions').send(validTransfer);
    expect(res.status).toBe(201);
    expect(res.body).toMatchObject({ ...validTransfer, status: 'completed' });
    expect(res.body.id).toBeDefined();
    expect(res.body.timestamp).toBeDefined();
  });

  test('returns 400 for invalid amount', async () => {
    const res = await request(app).post('/transactions').send({ ...validTransfer, amount: -5 });
    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Validation failed');
    expect(res.body.details).toBeInstanceOf(Array);
  });

  test('returns 400 for invalid account format', async () => {
    const res = await request(app).post('/transactions').send({ ...validTransfer, fromAccount: 'BADFORMAT' });
    expect(res.status).toBe(400);
    expect(res.body.details.some(d => d.field === 'fromAccount')).toBe(true);
  });

  test('returns 400 for invalid currency', async () => {
    const res = await request(app).post('/transactions').send({ ...validTransfer, currency: 'XYZ' });
    expect(res.status).toBe(400);
    expect(res.body.details.some(d => d.field === 'currency')).toBe(true);
  });

  test('creates deposit without fromAccount', async () => {
    const res = await request(app).post('/transactions').send({
      toAccount: 'ACC-00001',
      amount: 200,
      currency: 'EUR',
      type: 'deposit',
    });
    expect(res.status).toBe(201);
    expect(res.body.type).toBe('deposit');
  });
});

describe('GET /transactions', () => {
  test('returns empty array when no transactions', async () => {
    const res = await request(app).get('/transactions');
    expect(res.status).toBe(200);
    expect(res.body).toEqual([]);
  });

  test('returns all transactions', async () => {
    await request(app).post('/transactions').send({ fromAccount: 'ACC-12345', toAccount: 'ACC-67890', amount: 10, currency: 'USD', type: 'transfer' });
    await request(app).post('/transactions').send({ toAccount: 'ACC-00001', amount: 50, currency: 'EUR', type: 'deposit' });
    const res = await request(app).get('/transactions');
    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(2);
  });
});

describe('GET /transactions/:id', () => {
  test('returns transaction by id', async () => {
    const create = await request(app).post('/transactions').send({ fromAccount: 'ACC-12345', toAccount: 'ACC-67890', amount: 10, currency: 'USD', type: 'transfer' });
    const id = create.body.id;
    const res = await request(app).get(`/transactions/${id}`);
    expect(res.status).toBe(200);
    expect(res.body.id).toBe(id);
  });

  test('returns 404 for unknown id', async () => {
    const res = await request(app).get('/transactions/nonexistent-id');
    expect(res.status).toBe(404);
  });
});

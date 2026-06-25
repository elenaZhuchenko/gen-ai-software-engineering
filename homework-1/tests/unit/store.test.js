const store = require('../../src/store');

beforeEach(() => store.clear());

describe('store.add', () => {
  test('stores a transaction and returns it', () => {
    const tx = { id: '1', fromAccount: 'ACC-00001', amount: 10 };
    const result = store.add(tx);
    expect(result).toEqual(tx);
    expect(store.getAll()).toHaveLength(1);
  });
});

describe('store.getAll', () => {
  test('returns empty array when no transactions', () => {
    expect(store.getAll()).toEqual([]);
  });

  test('returns all stored transactions', () => {
    store.add({ id: '1' });
    store.add({ id: '2' });
    expect(store.getAll()).toHaveLength(2);
  });
});

describe('store.getById', () => {
  test('returns transaction by id', () => {
    store.add({ id: 'abc', amount: 50 });
    expect(store.getById('abc')).toMatchObject({ id: 'abc', amount: 50 });
  });

  test('returns null when id not found', () => {
    expect(store.getById('missing')).toBeNull();
  });
});

describe('store.clear', () => {
  test('removes all transactions', () => {
    store.add({ id: '1' });
    store.clear();
    expect(store.getAll()).toEqual([]);
  });
});

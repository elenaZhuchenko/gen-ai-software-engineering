const { validate } = require('../../src/validators/transactionValidator');

describe('amount validation', () => {
  test('rejects missing amount', () => {
    const errors = validate({ fromAccount: 'ACC-00001', toAccount: 'ACC-00002', currency: 'USD', type: 'transfer' });
    expect(errors.some(e => e.field === 'amount')).toBe(true);
  });

  test('rejects zero amount', () => {
    const errors = validate({ fromAccount: 'ACC-00001', toAccount: 'ACC-00002', amount: 0, currency: 'USD', type: 'transfer' });
    expect(errors.some(e => e.field === 'amount')).toBe(true);
  });

  test('rejects negative amount', () => {
    const errors = validate({ fromAccount: 'ACC-00001', toAccount: 'ACC-00002', amount: -5, currency: 'USD', type: 'transfer' });
    expect(errors.some(e => e.field === 'amount')).toBe(true);
  });

  test('rejects more than 2 decimal places', () => {
    const errors = validate({ fromAccount: 'ACC-00001', toAccount: 'ACC-00002', amount: 1.123, currency: 'USD', type: 'transfer' });
    expect(errors.some(e => e.field === 'amount')).toBe(true);
  });

  test('accepts valid amount', () => {
    const errors = validate({ fromAccount: 'ACC-00001', toAccount: 'ACC-00002', amount: 100.50, currency: 'USD', type: 'transfer' });
    expect(errors.some(e => e.field === 'amount')).toBe(false);
  });
});

describe('account format validation', () => {
  test('rejects invalid fromAccount format', () => {
    const errors = validate({ fromAccount: 'INVALID', toAccount: 'ACC-00002', amount: 10, currency: 'USD', type: 'transfer' });
    expect(errors.some(e => e.field === 'fromAccount')).toBe(true);
  });

  test('rejects invalid toAccount format', () => {
    const errors = validate({ fromAccount: 'ACC-00001', toAccount: '12345', amount: 10, currency: 'USD', type: 'transfer' });
    expect(errors.some(e => e.field === 'toAccount')).toBe(true);
  });

  test('accepts valid account format ACC-XXXXX', () => {
    const errors = validate({ fromAccount: 'ACC-12345', toAccount: 'ACC-ABCDE', amount: 10, currency: 'USD', type: 'transfer' });
    expect(errors.some(e => e.field === 'fromAccount' || e.field === 'toAccount')).toBe(false);
  });

  test('deposit does not require fromAccount', () => {
    const errors = validate({ toAccount: 'ACC-00001', amount: 10, currency: 'USD', type: 'deposit' });
    expect(errors.some(e => e.field === 'fromAccount')).toBe(false);
  });

  test('withdrawal does not require toAccount', () => {
    const errors = validate({ fromAccount: 'ACC-00001', amount: 10, currency: 'USD', type: 'withdrawal' });
    expect(errors.some(e => e.field === 'toAccount')).toBe(false);
  });
});

describe('currency validation', () => {
  test('rejects invalid currency code', () => {
    const errors = validate({ fromAccount: 'ACC-00001', toAccount: 'ACC-00002', amount: 10, currency: 'XYZ', type: 'transfer' });
    expect(errors.some(e => e.field === 'currency')).toBe(true);
  });

  test('accepts USD', () => {
    const errors = validate({ fromAccount: 'ACC-00001', toAccount: 'ACC-00002', amount: 10, currency: 'USD', type: 'transfer' });
    expect(errors.some(e => e.field === 'currency')).toBe(false);
  });

  test('accepts EUR', () => {
    const errors = validate({ fromAccount: 'ACC-00001', toAccount: 'ACC-00002', amount: 10, currency: 'EUR', type: 'transfer' });
    expect(errors.some(e => e.field === 'currency')).toBe(false);
  });
});

describe('type validation', () => {
  test('rejects invalid type', () => {
    const errors = validate({ fromAccount: 'ACC-00001', toAccount: 'ACC-00002', amount: 10, currency: 'USD', type: 'invalid' });
    expect(errors.some(e => e.field === 'type')).toBe(true);
  });

  test('accepts deposit', () => {
    const errors = validate({ toAccount: 'ACC-00001', amount: 10, currency: 'USD', type: 'deposit' });
    expect(errors.some(e => e.field === 'type')).toBe(false);
  });
});

describe('valid transaction returns no errors', () => {
  test('complete valid transfer returns empty errors', () => {
    const errors = validate({ fromAccount: 'ACC-12345', toAccount: 'ACC-67890', amount: 100.50, currency: 'USD', type: 'transfer' });
    expect(errors).toEqual([]);
  });
});

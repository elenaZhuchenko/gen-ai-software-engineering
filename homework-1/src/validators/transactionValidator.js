'use strict';

const { isValidCurrency } = require('../utils/currency');

const ACCOUNT_REGEX = /^ACC-[A-Z0-9]{5}$/i;
const VALID_TYPES = new Set(['deposit', 'withdrawal', 'transfer']);

function validate(body) {
  const errors = [];
  const { fromAccount, toAccount, amount, currency, type } = body;

  // type
  if (!type || !VALID_TYPES.has(type)) {
    errors.push({ field: 'type', message: 'Type must be deposit, withdrawal, or transfer' });
  }

  // amount
  if (amount === undefined || amount === null) {
    errors.push({ field: 'amount', message: 'Amount is required' });
  } else if (typeof amount !== 'number' || amount <= 0) {
    errors.push({ field: 'amount', message: 'Amount must be a positive number' });
  } else if (!/^\d+(\.\d{1,2})?$/.test(String(amount))) {
    errors.push({ field: 'amount', message: 'Amount must have at most 2 decimal places' });
  }

  // currency
  if (!currency) {
    errors.push({ field: 'currency', message: 'Currency is required' });
  } else if (!isValidCurrency(currency)) {
    errors.push({ field: 'currency', message: 'Invalid currency code' });
  }

  // accounts
  const needsFrom = type === 'withdrawal' || type === 'transfer';
  const needsTo = type === 'deposit' || type === 'transfer';

  if (needsFrom) {
    if (!fromAccount) {
      errors.push({ field: 'fromAccount', message: 'fromAccount is required for withdrawal/transfer' });
    } else if (!ACCOUNT_REGEX.test(fromAccount)) {
      errors.push({ field: 'fromAccount', message: 'Account must follow format ACC-XXXXX' });
    }
  } else if (fromAccount && !ACCOUNT_REGEX.test(fromAccount)) {
    errors.push({ field: 'fromAccount', message: 'Account must follow format ACC-XXXXX' });
  }

  if (needsTo) {
    if (!toAccount) {
      errors.push({ field: 'toAccount', message: 'toAccount is required for deposit/transfer' });
    } else if (!ACCOUNT_REGEX.test(toAccount)) {
      errors.push({ field: 'toAccount', message: 'Account must follow format ACC-XXXXX' });
    }
  } else if (toAccount && !ACCOUNT_REGEX.test(toAccount)) {
    errors.push({ field: 'toAccount', message: 'Account must follow format ACC-XXXXX' });
  }

  return errors;
}

module.exports = { validate };

'use strict';

const express = require('express');
const { v4: uuidv4 } = require('uuid');
const store = require('../store');
const { validate } = require('../validators/transactionValidator');

const router = express.Router();

router.post('/', (req, res) => {
  const errors = validate(req.body);
  if (errors.length > 0) {
    return res.status(400).json({ error: 'Validation failed', details: errors });
  }

  const transaction = {
    id: uuidv4(),
    fromAccount: req.body.fromAccount ?? null,
    toAccount: req.body.toAccount ?? null,
    amount: req.body.amount,
    currency: req.body.currency.toUpperCase(),
    type: req.body.type,
    timestamp: new Date().toISOString(),
    status: 'completed',
  };

  store.add(transaction);
  return res.status(201).json(transaction);
});

router.get('/', (req, res) => {
  const { accountId, type, from, to } = req.query;
  let txs = store.getAll();

  if (accountId) {
    txs = txs.filter(tx => tx.fromAccount === accountId || tx.toAccount === accountId);
  }

  if (type) {
    txs = txs.filter(tx => tx.type === type);
  }

  if (from) {
    const fromDate = new Date(from);
    txs = txs.filter(tx => new Date(tx.timestamp) >= fromDate);
  }

  if (to) {
    const toDate = new Date(to);
    toDate.setHours(23, 59, 59, 999);
    txs = txs.filter(tx => new Date(tx.timestamp) <= toDate);
  }

  return res.json(txs);
});

router.get('/:id', (req, res) => {
  const tx = store.getById(req.params.id);
  if (!tx) {
    return res.status(404).json({ error: 'Transaction not found' });
  }
  return res.json(tx);
});

module.exports = router;

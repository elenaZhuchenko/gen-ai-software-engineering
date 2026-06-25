'use strict';

const express = require('express');
const store = require('../store');

const router = express.Router();
const ACCOUNT_REGEX = /^ACC-[A-Z0-9]{5}$/i;

router.get('/:accountId/balance', (req, res) => {
  const { accountId } = req.params;

  if (!ACCOUNT_REGEX.test(accountId)) {
    return res.status(400).json({ error: 'Invalid account ID format. Must be ACC-XXXXX' });
  }

  const txs = store.getAll().filter(
    tx => tx.fromAccount === accountId || tx.toAccount === accountId
  );

  const balance = txs.reduce((acc, tx) => {
    if (tx.toAccount === accountId) return acc + tx.amount;
    if (tx.fromAccount === accountId) return acc - tx.amount;
    return acc;
  }, 0);

  return res.json({ accountId, balance: Math.round(balance * 100) / 100, currency: 'USD' });
});

router.get('/:accountId/summary', (req, res) => {
  const { accountId } = req.params;

  if (!ACCOUNT_REGEX.test(accountId)) {
    return res.status(400).json({ error: 'Invalid account ID format. Must be ACC-XXXXX' });
  }

  const txs = store.getAll().filter(
    tx => tx.fromAccount === accountId || tx.toAccount === accountId
  );

  const totalDeposits = txs
    .filter(tx => tx.type === 'deposit' && tx.toAccount === accountId)
    .reduce((sum, tx) => sum + tx.amount, 0);

  const totalWithdrawals = txs
    .filter(tx => tx.type === 'withdrawal' && tx.fromAccount === accountId)
    .reduce((sum, tx) => sum + tx.amount, 0);

  const mostRecentDate = txs.length > 0
    ? txs.reduce((latest, tx) => (tx.timestamp > latest ? tx.timestamp : latest), txs[0].timestamp)
    : null;

  return res.json({
    accountId,
    totalDeposits: Math.round(totalDeposits * 100) / 100,
    totalWithdrawals: Math.round(totalWithdrawals * 100) / 100,
    transactionCount: txs.length,
    mostRecentTransactionDate: mostRecentDate,
  });
});

module.exports = router;

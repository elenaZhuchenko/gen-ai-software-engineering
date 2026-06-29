'use strict';

const express = require('express');
const transactionRoutes = require('./routes/transactions');
const accountRoutes = require('./routes/accounts');

const app = express();

app.use(express.json());

app.get('/', (_, res) => res.json({
  name: 'Banking Transactions API',
  version: '1.0.0',
  endpoints: [
    'POST   /transactions',
    'GET    /transactions',
    'GET    /transactions/:id',
    'GET    /transactions/export?format=csv',
    'GET    /accounts/:accountId/balance',
    'GET    /accounts/:accountId/summary',
  ],
}));

app.get('/health', (_, res) => res.json({ status: 'ok' }));
app.use('/transactions', transactionRoutes);
app.use('/accounts', accountRoutes);

app.use((req, res) => res.status(404).json({ error: 'Route not found' }));

module.exports = app;

'use strict';

const express = require('express');
const transactionRoutes = require('./routes/transactions');
const accountRoutes = require('./routes/accounts');

const app = express();

app.use(express.json());

app.get('/health', (_, res) => res.json({ status: 'ok' }));
app.use('/transactions', transactionRoutes);
app.use('/accounts', accountRoutes);

app.use((req, res) => res.status(404).json({ error: 'Route not found' }));

module.exports = app;

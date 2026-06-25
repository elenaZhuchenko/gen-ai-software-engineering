'use strict';

let transactions = [];

const store = {
  add(transaction) {
    transactions.push(transaction);
    return transaction;
  },

  getAll() {
    return [...transactions];
  },

  getById(id) {
    return transactions.find(tx => tx.id === id) ?? null;
  },

  clear() {
    transactions = [];
  },
};

module.exports = store;

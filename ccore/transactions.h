#pragma once
#include "transaction.h"

typedef struct {
    unsigned int count;
    Transaction **txns;
} TransactionList;

void
transactions_init(TransactionList *txns);

void
transactions_deinit(TransactionList *txns);

void
transactions_add(TransactionList *txns, Transaction *txn);

/* Returns a NULL-terminated list of txns with specified date
 *
 * The resulting list must be freed with free(). Returns NULL if there's no
 * matching txn.
 */
Transaction**
transactions_at_date(TransactionList *txns, time_t date);

int
transactions_find(TransactionList *txns, Transaction *txn);

bool
transactions_remove(TransactionList *txns, Transaction *txn);

void
transactions_sort(TransactionList *txns);
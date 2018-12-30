#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include "accounts.h"
#include "util.h"

/* AccountList public */
void
accounts_init(AccountList *accounts, Currency *default_currency)
{
    accounts->default_currency = default_currency;
    accounts->accounts = NULL;
    accounts->count = 0;
    accounts->a2entries = g_hash_table_new(g_str_hash, g_str_equal);
}

void
accounts_deinit(AccountList *accounts)
{
    GHashTableIter iter;
    g_hash_table_iter_init(&iter, accounts->a2entries);
    gpointer _, entries;
    while (g_hash_table_iter_next(&iter, &_, &entries)) {
        free(entries);
    }
    g_hash_table_destroy(accounts->a2entries);

    for (int i=0; i<accounts->count; i++) {
        account_deinit(accounts->accounts[i]);
        free(accounts->accounts[i]);
    }
    free(accounts->accounts);
}

bool
accounts_copy(AccountList *dst, const AccountList *src)
{
    accounts_init(dst, src->default_currency);
    for (int i=0; i<src->count; i++) {
        Account *a = accounts_create(dst);
        if (!account_copy(a, src->accounts[i])) {
            accounts_deinit(dst);
            return false;
        }
    }
    return true;
}

Account*
accounts_create(AccountList *accounts)
{
    Account *res = calloc(1, sizeof(Account));
    accounts->count++;
    accounts->accounts = realloc(
        accounts->accounts, sizeof(Account*) * accounts->count);
    accounts->accounts[accounts->count-1] = res;
    return res;
}

EntryList*
accounts_entries_for_account(AccountList *accounts, Account *account)
{
    EntryList *entries = g_hash_table_lookup(accounts->a2entries, account->name);
    if (entries == NULL) {
        entries = malloc(sizeof(EntryList));
        entries_init(entries, account);
        g_hash_table_insert(accounts->a2entries, account->name, entries);
    }
    return entries;
}

bool
accounts_remove(AccountList *accounts, Account *target)
{
    int index = -1;
    for (int i=0; i<accounts->count; i++) {
        if (accounts->accounts[i] == target) {
            index = i;
            break;
        }
    }
    if (index == -1) {
        // bad pointer
        return false;
    }
    // we have to move memory around
    memmove(
        &accounts->accounts[index],
        &accounts->accounts[index+1],
        sizeof(Account*) * (accounts->count - index - 1));
    accounts->count--;
    accounts->accounts = realloc(
        accounts->accounts, sizeof(Account*) * accounts->count);
    /* Normally, we should be freeing our account here. However, because of the
     * Undoer, we can't: it holds a reference to the deleted account and needs
     * it around in case we need it again. The best option at this time is
     * simply to never free our accounts. When the Undoer will be converted to
     * C, we can revisit our memory management model to free Accounts when it's
     * safe.
     */
    /*free(target);*/
    return true;
}

bool
accounts_rename(AccountList *accounts, Account *target, const char *newname)
{
    Account *found = accounts_find_by_name(accounts, newname);
    if (found != NULL && found != target) {
        return false;
    }
    EntryList *entries = g_hash_table_lookup(accounts->a2entries, target->name);
    if (entries != NULL) {
        g_hash_table_remove(accounts->a2entries, target->name);
    }
    account_name_set(target, newname);
    if (entries != NULL) {
        g_hash_table_insert(accounts->a2entries, target->name, entries);
    }
    return true;
}

Account *
accounts_find_by_name(const AccountList *accounts, const char *name)
{
    if (name == NULL) {
        return NULL;
    }
    Account *res = NULL;
    char *dst = NULL;
    const char *trimmed;
    if (strstrip(&dst, name)) {
        trimmed = dst;
    } else {
        trimmed = name;
    }
    gchar *casefold = g_utf8_casefold(trimmed, -1);
    gchar *key = g_utf8_collate_key(casefold, -1);
    g_free(casefold);
    for (int i=0; i<accounts->count; i++) {
        Account *a = accounts->accounts[i];
        if (strcmp(key, a->name_key) == 0) {
            res = a;
            break;
        }
        if (a->account_number != NULL && strcmp(trimmed, a->account_number) == 0) {
            res = a;
            break;
        }
    }
    if (dst != NULL) {
        free(dst);
    }
    g_free(key);
    return res;
}

Account*
accounts_find_by_reference(const AccountList *accounts, const char *reference)
{
    if ((reference == NULL) || (strlen(reference) == 0)) {
        return NULL;
    }
    for (int i=0; i<accounts->count; i++) {
        Account *a = accounts->accounts[i];
        if (strcmp(reference, a->reference) == 0) {
            return a;
        }
    }
    return NULL;
}

#pragma once
#include <stdbool.h>
#include <time.h>

#define CURRENCY_CODE_MAXLEN 4
#define CURRENCY_MAX_EXPONENT 10

typedef struct {
    char code[CURRENCY_CODE_MAXLEN+1];
    unsigned int exponent;
    time_t start_date;
    double start_rate;
    time_t stop_date;
    double latest_rate;
} Currency;

typedef enum {
    CURRENCY_OK = 0,
    CURRENCY_NORESULT = 1,
    CURRENCY_ERROR = 2,
} CurrencyResult;

CurrencyResult
currency_global_init(char *dbpath);

CurrencyResult
currency_global_reset_currencies(void);

void
currency_global_deinit(void);

Currency*
currency_register(
    char *code,
    unsigned int exponent,
    time_t start_date,
    double start_rate,
    time_t stop_date,
    double latest_rate);

Currency*
currency_get(const char *code);

CurrencyResult
currency_getrate(time_t date, Currency *c1, Currency *c2, double *result);

void
currency_set_CAD_value(time_t date, Currency *currency, double value);

bool
currency_daterange(Currency *currency, time_t *start, time_t *stop);

#ifndef STACK_ANALYSIS_STDLIB_H
#define STACK_ANALYSIS_STDLIB_H
#include <stddef.h>
void abort(void);
int abs(int n);
void *calloc(size_t count, size_t size);
void free(void *ptr);
void *malloc(size_t size);
void qsort(void *base, size_t nmemb, size_t size,
           int (*compar)(const void *, const void *));
void *realloc(void *ptr, size_t size);
long strtol(const char *nptr, char **endptr, int base);
unsigned long strtoul(const char *nptr, char **endptr, int base);
#endif

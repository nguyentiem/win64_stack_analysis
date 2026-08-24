#ifndef STACK_ANALYSIS_STDIO_H
#define STACK_ANALYSIS_STDIO_H
#include <stddef.h>
#include <stdarg.h>
int printf(const char *format, ...);
int vprintf(const char *format, va_list args);
int snprintf(char *s, size_t n, const char *format, ...);
int sscanf(const char *s, const char *format, ...);
#endif

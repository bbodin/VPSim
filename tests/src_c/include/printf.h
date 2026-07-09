#ifndef  _PRINTF_UTIL_
#define _PRINTF_UTIL_

#include "uart.h"


// Simple helper to convert integer to decimal string
void itoa_dec(unsigned int value, char *buf) {
    char temp[12]; // enough for 32-bit int
    int i = 0;
    if (value == 0) {
        buf[0] = '0';
        buf[1] = 0;
        return;
    }
    while (value > 0) {
        temp[i++] = '0' + (value % 10);
        value /= 10;
    }
    // reverse string
    int j;
    for (j = 0; j < i; j++) {
        buf[j] = temp[i - 1 - j];
    }
    buf[i] = 0;
}

// Simple helper to convert pointer to hex string like 0x1234
void ptr_to_hex(void *ptr, char *buf) {
    unsigned long val = (unsigned long)ptr;
    const char hex_chars[] = "0123456789ABCDEF";
    buf[0] = '0';
    buf[1] = 'x';
    for (long unsigned  i = 0; i < (sizeof(void*)*2); i++) {
        buf[2 + sizeof(void*)*2 - 1 - i] = hex_chars[val & 0xF];
        val >>= 4;
    }
    buf[2 + sizeof(void*)*2] = 0;
}


// Simple printf replacement using only uart_send_string
void printf_str(const char *s) {
    uart_send_string(s);
}

void printf_char(char c) {
    char buf[2] = {c, 0};
    uart_send_string(buf);
}

void printf_hex(unsigned long n)
{
    const char hex_digits[] = "0123456789ABCDEF";
    char buf[16];
    int i = 0;

    if (n == 0) {
        printf_char('0');
        return;
    }

    while (n > 0) {
        buf[i++] = hex_digits[n & 0xF];  // lowest hex digit
        n >>= 4;                         // shift right 4 bits
    }

    // Print in reverse order
    for (int j = i - 1; j >= 0; j--) {
        printf_char(buf[j]);
    }
}


void print_uint(unsigned long n) {
    char buf[20];   // enough for 64-bit
    int i = 0;

    if (n == 0) {
        printf_char('0');
        return;
    }

    while (n > 0) {
        buf[i++] = '0' + (n % 10);
        n /= 10;
    }

    // Digits are in reverse order
    for (int j = i - 1; j >= 0; j--) {
        printf_char(buf[j]);
    }
}

#endif
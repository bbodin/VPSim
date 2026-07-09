#ifndef  _UART_UTIL_
#define _UART_UTIL_

volatile unsigned int * const UART0DR = (unsigned int *) 0x09000000;

static inline void uart_send_char(char c) {
     *UART0DR = (unsigned int)(c);
}

// Helper function to print a string over UART
static inline void uart_send_string(const char *s) {
    while(*s != '\0') {
        uart_send_char(*s++);
    }
}

// Main function to convert int to string and print via UART
static inline void uart_send_integer(unsigned value) {
    char buffer[12]; // Enough for 32-bit signed int (-2147483648 to 2147483647)
    int i = 0;

    if (value == 0) {
        uart_send_char('0');
        return;
    }

    // Convert to string in reverse
    while (value > 0) {
        buffer[i++] = (value % 10) + '0';
        value /= 10;
    }

    // Print in correct order
    while (i--) {
        uart_send_char(buffer[i]);
    }
}

#endif
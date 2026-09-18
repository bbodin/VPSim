#ifndef __SESAM__
#define __SESAM__

#include <stdint.h>
#include <string.h>

#define sesam_mem ((volatile uint8_t *)0x17000000)


/* SESAM operation constants */
#define SESAMOP                 0x00
#define SESAMOP_SHOW            0x01
#define SESAMOP_QUIT            0x42
#define SESAMOP_START_BENCH     0x52
#define SESAMOP_END_BENCH       0x54
#define SESAMOP_LIST            0x20
#define SESAMOP_CLEAN_PARAMS    0x58
#define SESAMOP_START_PARAM     0x62
#define SESAMOP_END_PARAM       0x72
#define SESAMOP_EXECUTE_PARAMS  0x78

void sesam_reset_args() {
    sesam_mem[0] = SESAMOP_CLEAN_PARAMS; // reset strParam
}

void sesam_exec_params() {
    sesam_mem[0] = SESAMOP_EXECUTE_PARAMS;
}

void sesam_start_benchmark() {
    sesam_mem[0] = SESAMOP_START_BENCH; 
}

void sesam_end_benchmark() {
    sesam_mem[0] = SESAMOP_END_BENCH; 
}

void sesam_list() {
    sesam_mem[0] = SESAMOP_LIST;
}

void sesam_quit() {
    sesam_mem[0] = SESAMOP_QUIT;
}

void sesam_push_string(const char *str) {
    sesam_mem[0] = SESAMOP_START_PARAM;       // new string
    for (int i = 0; str[i] != '\0'; i++) {
        sesam_mem[1] = str[i]; // append
    }
    sesam_mem[0] = SESAMOP_END_PARAM;       // push
}

int sesam_collect_output(char *buffer, int max_len) {
    int i = 0;
    int safety = 1024;  // prevent infinite loop

    while (i < max_len - 1 && safety-- > 0) {
        char c = sesam_mem[1];  // read next char from SESAM

        if (c == 0)
            break;

        buffer[i++] = c;
    }

    buffer[i] = '\0';  // null terminate
    return i;          // number of chars read
}

void sesam_snapshot(const char *name) {
    sesam_reset_args();
    sesam_push_string("snapshot");
    sesam_push_string(name);
    sesam_exec_params();
}

double sesam_get_perf(const char *context, const char *name) {

    char buf[512];
    sesam_reset_args();
    sesam_push_string("get-perf");
    sesam_push_string(context);
    sesam_push_string(name);
    sesam_exec_params();

    return 0.0;

    sesam_collect_output(buf, sizeof(buf));

    // Expected line format:
    // context.name = value
    char pattern[256];
    int pi = 0;
    for (int i = 0; context[i]; i++) pattern[pi++] = context[i];
    pattern[pi++] = '.';
    for (int i = 0; name[i]; i++) pattern[pi++] = name[i];
    pattern[pi++] = ' ';
    pattern[pi++] = '=';
    pattern[pi++] = ' ';
    pattern[pi] = '\0';

    char *pos = strstr(buf, pattern);
    if (!pos) {
        return -1.0f;  // not found
    }   
    // move pointer after " = "
    pos += strlen(pattern);

    // convert value
    return atof(pos);
}

void sesam_start_bench_simple(const char *name) {
    sesam_reset_args();
    sesam_push_string(name);
    sesam_start_benchmark();
}

void sesam_end_bench_simple() {
    sesam_end_benchmark();
}

void loop_forever(void)
{
    while (1) {
        // Optional: place low-power sleep instruction or NOP
        __asm__("nop");
    }
}

#endif // __SESAM__
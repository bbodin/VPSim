#ifndef SESAM_H
#define SESAM_H

#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>

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

/* Global variables for SESAM memory mapping */
extern void *sesam_mem;
extern int fd;

/* Function prototypes */
void map_sesam_mem(void);
void unmap_sesam(void);


/* Inline function implementations */
static inline void sesam_reset_args(void) {
    *((uint8_t *)sesam_mem) = SESAMOP_CLEAN_PARAMS;
}

static inline void sesam_exec_params(void) {
    *((uint8_t *)sesam_mem) = SESAMOP_EXECUTE_PARAMS;
}

static inline void sesam_start_benchmark(void) {
    *((uint8_t *)sesam_mem) = SESAMOP_START_BENCH;
}

static inline void sesam_end_benchmark(void) {
    *((uint8_t *)sesam_mem) = SESAMOP_END_BENCH;
}

static inline void sesam_list(void) {
    *((uint8_t *)sesam_mem) = SESAMOP_LIST;
}

static inline void sesam_quit(void) {
    *((uint8_t *)sesam_mem) = SESAMOP_QUIT;
}

static inline void sesam_push_string(const char *str) {
    *((uint8_t *)sesam_mem) = SESAMOP_START_PARAM;
    for (int i = 0; str[i] != '\0'; i++) {
        *((uint8_t *)sesam_mem + 1) = str[i];
    }
    *((uint8_t *)sesam_mem) = SESAMOP_END_PARAM;
}

static inline void sesam_snapshot(const char *name) {
    sesam_reset_args();
    sesam_push_string("snapshot");
    sesam_push_string(name);
    sesam_exec_params();
}

static inline void sesam_start_bench_simple(const char *name) {
    sesam_reset_args();
    sesam_push_string(name);
    sesam_start_benchmark();
}

static inline void sesam_end_bench_simple(void) {
    sesam_end_benchmark();
}

#endif /* SESAM_H */
